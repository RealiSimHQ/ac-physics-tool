// AC Physics Swapper - Client-side app
// RealiSimHQ 2026

// ─── Patreon Auth ───
const PATREON_CLIENT_ID = 'vq1EOHIoQ_2p_R0SVEcW3FRYvbMkcwMX1utj5hcvipJ3_1sSPethC5KM2FoiHZgS';
const PATREON_REDIRECT = 'https://realisimhq.github.io/ac-physics-tool/callback.html';

function patreonLogin() {
    const returnUrl = encodeURIComponent(window.location.origin + window.location.pathname);
    const url = `https://www.patreon.com/oauth2/authorize?response_type=code&client_id=${PATREON_CLIENT_ID}&redirect_uri=${encodeURIComponent(PATREON_REDIRECT)}&scope=identity%20identity%5Bemail%5D%20identity.memberships&state=${returnUrl}`;
    window.location.href = url;
}

function checkPatreonSession() {
    const auth = sessionStorage.getItem('patreon_authorized');
    const until = parseInt(sessionStorage.getItem('patreon_until') || '0');
    if (auth === 'true' && Date.now() < until) return sessionStorage.getItem('patreon_name') || 'Patron';
    return null;
}

function hasUsedTrial() {
    return localStorage.getItem('dpe_trial_used') === 'true';
}

function markTrialUsed() {
    localStorage.setItem('dpe_trial_used', 'true');
}

function initPatreonGate() {
    const patron = checkPatreonSession();
    const gate = document.getElementById('patreon-gate');
    const uploadSection = document.getElementById('upload-section');
    if (patron) {
        gate.classList.add('hidden');
        const welcome = document.createElement('div');
        welcome.className = 'patron-welcome';
        welcome.textContent = `Welcome, ${patron}! 🎉`;
        gate.parentNode.insertBefore(welcome, document.getElementById('car-info'));
    } else if (!hasUsedTrial()) {
        // Free trial
        gate.innerHTML = `<div class="gate-card" style="border-color:var(--accent-cyan);padding:20px;">
            <p style="margin:0;color:var(--accent-cyan);">🎁 <strong>Free Trial</strong> — Generate one physics pack free. <a href="https://www.patreon.com/checkout/RealiSimHQ?rid=26118508" target="_blank" style="color:var(--accent-gold);">Subscribe for unlimited access</a></p>
        </div>`;
    } else {
        // Trial used
        uploadSection.classList.remove('active');
        uploadSection.style.display = 'none';
        document.getElementById('pack-section').style.display = 'none';
        document.getElementById('generate-section').style.display = 'none';
        document.getElementById('advanced-section').style.display = 'none';
        gate.querySelector('h3').textContent = '🔒 Trial Used';
        gate.querySelector('p').textContent = 'You\'ve used your free generation. Subscribe to continue using the tool.';
    }
}

const State = {
    packs: [],
    selectedPack: null,
    originalCar: {
        files: {},
        metadata: {}
    },
    donorCar: null,
    matchedDonor: null
};

// INI Parser
class INIParser {
    static parse(content) {
        const result = {};
        let currentSection = null;
        
        const lines = content.split('\n');
        for (let line of lines) {
            line = line.trim();
            
            // Skip empty lines and comments
            if (!line || line.startsWith(';') || line.startsWith('#')) {
                continue;
            }
            
            // Section header
            if (line.startsWith('[') && line.endsWith(']')) {
                currentSection = line.slice(1, -1);
                if (!result[currentSection]) {
                    result[currentSection] = {};
                }
                continue;
            }
            
            // Key=value pair
            if (line.includes('=') && currentSection) {
                const [key, ...valueParts] = line.split('=');
                let value = valueParts.join('=').trim();
                
                // Strip inline comments
                value = value.split(';')[0].split('\t')[0].trim();
                
                result[currentSection][key.trim()] = value;
            }
        }
        
        return result;
    }
    
    static serialize(data) {
        let output = '';
        
        for (const [section, pairs] of Object.entries(data)) {
            output += `[${section}]\n`;
            for (const [key, value] of Object.entries(pairs)) {
                output += `${key}=${value}\n`;
            }
            output += '\n';
        }
        
        return output;
    }
}

// Initialize app
async function init() {
    try {
        // Load pack index
        const response = await fetch('data/packs.json');
        State.packs = await response.json();
        
        renderPackGrid();
        setupEventListeners();
    } catch (error) {
        console.error('Failed to initialize:', error);
        alert('Failed to load carpack data. Please refresh the page.');
    }
}

function renderPackGrid() {
    const grid = document.getElementById('pack-grid');
    grid.innerHTML = '';
    
    State.packs.forEach(pack => {
        const card = document.createElement('div');
        card.className = 'pack-card';
        card.dataset.packId = pack.id;
        
        // Determine logo extension
        const logoExt = pack.id === 'NNTS' ? 'jpg' : 'png';
        
        card.innerHTML = `
            <img src="logos/${pack.id}.${logoExt}" alt="${pack.name}" class="pack-logo">
            <h4>${pack.name}</h4>
<!-- -->
        `;
        
        card.addEventListener('click', () => selectPack(pack));
        grid.appendChild(card);
    });
}

function setupEventListeners() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    
    dropZone.addEventListener('click', () => fileInput.click());
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });
    
    dropZone.addEventListener('drop', async (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        
        const items = e.dataTransfer.items;
        await handleFileUpload(items);
    });
    
    fileInput.addEventListener('change', async (e) => {
        const files = e.target.files;
        await handleFilesArray(files);
    });
    
    document.getElementById('download-btn').addEventListener('click', generateSwap);
    
    // Advanced settings toggle
    document.getElementById('advanced-toggle').addEventListener('click', () => {
        const panel = document.getElementById('advanced-panel');
        const arrow = document.querySelector('.toggle-arrow');
        panel.classList.toggle('hidden');
        arrow.classList.toggle('open');
    });
    
    // Donor car manual selection
    document.getElementById('donor-select').addEventListener('change', (e) => {
        if (e.target.value && State.selectedPack) {
            State.matchedDonor = { carId: e.target.value, ...State.selectedPack.cars[e.target.value] };
        } else {
            findBestMatch();
        }
    });
}

async function handleFileUpload(items) {
    showLoading('Reading files...');
    
    try {
        const files = [];
        
        // Collect all entries first
        const entries = [];
        const rawFiles = [];
        
        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            if (item.kind === 'file') {
                const entry = item.webkitGetAsEntry ? item.webkitGetAsEntry() : null;
                if (entry) {
                    entries.push(entry);
                }
                // Always also grab the raw file as fallback
                const f = item.getAsFile();
                if (f) rawFiles.push(f);
            }
        }
        
        // Try to traverse directory entries
        if (entries.length > 0) {
            for (const entry of entries) {
                if (entry.isDirectory) {
                    console.log('[Swapper] Traversing directory:', entry.name);
                    await traverseEntry(entry, files, '');
                } else if (entry.isFile) {
                    await traverseEntry(entry, files, '');
                }
            }
        }
        
        console.log(`[Swapper] After traversal: ${files.length} files`);
        
        // If traversal gave us nothing, use raw files
        if (files.length === 0 && rawFiles.length > 0) {
            console.log('[Swapper] Falling back to raw files:', rawFiles.map(f => f.name));
            files.push(...rawFiles);
        }
        
        console.log(`[Swapper] Total ${files.length} files:`, files.map(f => f._fullPath || f.name));
        
        if (files.length === 0) {
            alert('No files found. Try dragging individual .ini files or a .zip instead.');
            return;
        }
        
        // Check for archives
        const zipFile = files.find(f => f.name.toLowerCase().endsWith('.zip'));
        const szFile = files.find(f => f.name.toLowerCase().endsWith('.7z'));
        const rarFile = files.find(f => f.name.toLowerCase().endsWith('.rar'));
        
        if (zipFile) {
            await processZipFile(zipFile);
        } else if (szFile || rarFile) {
            alert('Please extract your .7z or .rar file first, then drag the extracted data folder or files here.\n\nAlternatively, re-pack as a .zip file.');
        } else {
            await processCarFiles(files);
        }
    } catch (error) {
        console.error('Upload error:', error);
        alert('Error reading files: ' + error.message);
    } finally {
        hideLoading();
    }
}

async function handleFilesArray(fileList) {
    showLoading('Reading files...');
    
    try {
        const files = Array.from(fileList);
        
        const zipFile = files.find(f => f.name.toLowerCase().endsWith('.zip'));
        if (zipFile) {
            await processZipFile(zipFile);
        } else {
            await processCarFiles(files);
        }
    } catch (error) {
        console.error('Upload error:', error);
        alert('Error reading files: ' + error.message);
    } finally {
        hideLoading();
    }
}

function readAllEntries(reader) {
    return new Promise((resolve, reject) => {
        const allEntries = [];
        const readBatch = () => {
            reader.readEntries((batch) => {
                if (batch.length === 0) {
                    resolve(allEntries);
                } else {
                    allEntries.push(...batch);
                    readBatch();
                }
            }, reject);
        };
        readBatch();
    });
}

function getFileFromEntry(fileEntry) {
    return new Promise((resolve, reject) => {
        fileEntry.file(resolve, reject);
    });
}

async function traverseEntry(entry, files, path) {
    if (entry.isFile) {
        try {
            const file = await getFileFromEntry(entry);
            file._fullPath = path + file.name;
            files.push(file);
        } catch (err) {
            console.warn('[Swapper] Could not read file:', entry.fullPath, err);
        }
    } else if (entry.isDirectory) {
        const reader = entry.createReader();
        const newPath = path + entry.name + '/';
        
        try {
            const childEntries = await readAllEntries(reader);
            console.log(`[Swapper] Directory "${entry.name}" has ${childEntries.length} entries`);
            for (const childEntry of childEntries) {
                await traverseEntry(childEntry, files, newPath);
            }
        } catch (err) {
            console.warn('[Swapper] Could not read directory:', entry.fullPath, err);
        }
    }
}

async function processZipFile(file) {
    showLoading('Extracting ZIP...');
    const arrayBuffer = await file.arrayBuffer();
    const zip = await JSZip.loadAsync(arrayBuffer);
    
    const fileMap = {};
    
    for (const [zipPath, zipEntry] of Object.entries(zip.files)) {
        if (zipEntry.dir) continue;
        
        const fileName = zipPath.split('/').pop().toLowerCase();
        if (!fileName) continue;
        
        // Read as text for .ini/.lut/.rto, skip binary junk
        if (fileName.endsWith('.ini') || fileName.endsWith('.lut') || fileName.endsWith('.rto')) {
            const content = await zipEntry.async('string');
            fileMap[fileName] = content;
        }
    }
    
    State.originalCar.files = fileMap;
    State.originalCar.metadata = {};
    
    extractMetadata();
    
    if (!State.originalCar.files['car.ini'] || !State.originalCar.files['suspensions.ini'] || !State.originalCar.files['tyres.ini']) {
        alert('Missing required files (car.ini, suspensions.ini, tyres.ini). Make sure your ZIP contains these files.');
        return;
    }
    
    displayCarInfo();
    collapseUploadShowPacks();
}

async function processCarFiles(files) {
    State.originalCar.files = {};
    State.originalCar.metadata = {};
    
    // Read all files — accept any .ini/.lut/.rto regardless of folder structure
    for (const file of files) {
        const fileName = file.name.toLowerCase();
        
        if (fileName.endsWith('.ini') || fileName.endsWith('.lut') || fileName.endsWith('.rto')) {
            const content = await file.text();
            State.originalCar.files[fileName] = content;
        }
    }
    
    console.log('[Swapper] Parsed files:', Object.keys(State.originalCar.files));
    
    extractMetadata();
    
    if (!State.originalCar.files['car.ini'] || !State.originalCar.files['suspensions.ini'] || !State.originalCar.files['tyres.ini']) {
        const found = Object.keys(State.originalCar.files).join(', ') || 'none';
        alert(`Missing required files. Found: ${found}\n\nNeed: car.ini, suspensions.ini, tyres.ini\n\nTry dragging the contents of your data folder, or zip it first.`);
        return;
    }
    
    displayCarInfo();
    collapseUploadShowPacks();
}

function collapseUploadShowPacks() {
    // Hide full upload section
    deactivateStep('upload-section');
    document.getElementById('upload-section').classList.add('hidden');

    // Show collapsed upload dropdown
    const dd = document.getElementById('upload-dropdown');
    dd.classList.remove('hidden');
    document.getElementById('upload-dropdown-label').textContent =
        State.originalCar.metadata.name || 'Car loaded';

    // Toggle dropdown open/close
    document.getElementById('upload-dropdown-header').onclick = () => {
        document.getElementById('upload-dropdown-body').classList.toggle('hidden');
        dd.querySelector('.dropdown-arrow').classList.toggle('open');
    };

    // Setup mini drop zone
    setupMiniDropZone();

    // Show pack section with ta-da
    const packSection = document.getElementById('pack-section');
    packSection.classList.add('active');
    packSection.classList.add('tada-entrance');

    // Reset pack dropdown / generate if re-uploading
    document.getElementById('pack-dropdown').classList.add('hidden');
    deactivateStep('generate-section');
    deactivateStep('advanced-section');
    deactivateStep('visual-section');
}

function setupMiniDropZone() {
    const dz = document.getElementById('drop-zone-mini');
    const fi = document.getElementById('file-input-mini');
    if (!dz || dz._setup) return;
    dz._setup = true;
    dz.addEventListener('click', () => fi.click());
    dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('drag-over'); });
    dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
    dz.addEventListener('drop', async (e) => {
        e.preventDefault();
        dz.classList.remove('drag-over');
        await handleFileUpload(e.dataTransfer.items);
    });
    fi.addEventListener('change', async (e) => {
        await handleFilesArray(e.target.files);
    });
}

function collapsePacksShowGenerate() {
    // Add gold pulse ring to selected pack card
    document.querySelectorAll('.pack-card').forEach(card => {
        card.classList.remove('gold-selected');
    });
    const packId = State.selectedPack.packName.replace(/ /g, '_');
    const selectedCard = document.querySelector(`[data-pack-id="${packId}"]`);
    if (selectedCard) selectedCard.classList.add('gold-selected');

    // Show generate button with slide-up + pulse
    const genSection = document.getElementById('generate-section');
    genSection.classList.add('active');
    genSection.classList.add('slide-up-entrance');
    document.getElementById('download-btn').classList.add('btn-pulse-active');

    // Show advanced
    activateStep('advanced-section');
    activateStep('visual-section');
}

function renderPackGridInto(container) {
    container.innerHTML = '';
    State.packs.forEach(pack => {
        const card = document.createElement('div');
        card.className = 'pack-card';
        if (State.selectedPack && State.selectedPack.packName.replace(/ /g, '_') === pack.id) {
            card.classList.add('selected');
        }
        card.dataset.packId = pack.id;
        const logoExt = pack.id === 'NNTS' ? 'jpg' : 'png';
        card.innerHTML = `
            <img src="logos/${pack.id}.${logoExt}" alt="${pack.name}" class="pack-logo">
            <h4>${pack.name}</h4>
        `;
        card.addEventListener('click', () => selectPack(pack));
        container.appendChild(card);
    });
}

function extractMetadata() {
    if (State.originalCar.files['car.ini']) {
        const carData = INIParser.parse(State.originalCar.files['car.ini']);
        
        if (carData.BASIC) {
            State.originalCar.metadata.mass = parseFloat(carData.BASIC.TOTALMASS) || 0;
            State.originalCar.metadata.inertia = carData.BASIC.INERTIA;
            State.originalCar.metadata.graphicsOffset = carData.BASIC.GRAPHICS_OFFSET;
            State.originalCar.metadata.graphicsPitch = carData.BASIC.GRAPHICS_PITCH_ROTATION;
        }
        
        if (carData.INFO) {
            State.originalCar.metadata.name = carData.INFO.SCREEN_NAME || carData.INFO.SHORT_NAME || 'Unknown Car';
        }
    }
    
    if (State.originalCar.files['suspensions.ini']) {
        const suspData = INIParser.parse(State.originalCar.files['suspensions.ini']);
        
        if (suspData.BASIC) {
            State.originalCar.metadata.wheelbase = parseFloat(suspData.BASIC.WHEELBASE) || 0;
            State.originalCar.metadata.cgLocation = parseFloat(suspData.BASIC.CG_LOCATION) || 0;
        }
        
        if (suspData.FRONT) {
            State.originalCar.metadata.trackFront = parseFloat(suspData.FRONT.TRACK) || 0;
        }
        
        if (suspData.REAR) {
            State.originalCar.metadata.trackRear = parseFloat(suspData.REAR.TRACK) || 0;
        }
    }
    
    if (State.originalCar.files['tyres.ini']) {
        const tyresData = INIParser.parse(State.originalCar.files['tyres.ini']);
        
        if (tyresData.FRONT) {
            State.originalCar.metadata.radiusFront = parseFloat(tyresData.FRONT.RADIUS) || 0;
        }
        
        if (tyresData.REAR) {
            State.originalCar.metadata.radiusRear = parseFloat(tyresData.REAR.RADIUS) || 0;
        }
    }
}

function displayCarInfo() {
    const carInfo = document.getElementById('car-info');
    const metadata = State.originalCar.metadata;
    
    document.getElementById('car-name').textContent = metadata.name || '-';
    document.getElementById('car-mass').textContent = metadata.mass || '-';
    document.getElementById('car-wheelbase').textContent = metadata.wheelbase?.toFixed(2) || '-';
    
    const trackAvg = ((metadata.trackFront || 0) + (metadata.trackRear || 0)) / 2;
    document.getElementById('car-track').textContent = 
        `${metadata.trackFront?.toFixed(2) || '-'} / ${metadata.trackRear?.toFixed(2) || '-'}`;
    
    carInfo.classList.remove('hidden');
}

async function selectPack(pack) {
    showLoading(`Loading ${pack.name} carpack...`);
    
    try {
        // Remove previous selection
        document.querySelectorAll('.pack-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Mark selected
        document.querySelector(`[data-pack-id="${pack.id}"]`).classList.add('selected');
        
        // Load pack data
        const response = await fetch(`data/${pack.id}.json`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        State.selectedPack = await response.json();
        State.selectedPack.logo = `${pack.id}.${pack.id === 'NNTS' ? 'jpg' : 'png'}`;
        
        // Populate advanced dropdowns
        populateAdvancedDropdowns();
        
        // Find best match
        findBestMatch();
        
        // Collapse packs into dropdown, show generate button
        collapsePacksShowGenerate();
    } catch (error) {
        console.error('Failed to load pack:', error);
        alert('Failed to load carpack data.');
    } finally {
        hideLoading();
    }
}

function populateAdvancedDropdowns() {
    const donorSelect = document.getElementById('donor-select');
    const engineSelect = document.getElementById('engine-select');
    
    // Clear and add default options
    donorSelect.innerHTML = '<option value="">Auto (best match)</option>';
    engineSelect.innerHTML = '<option value="">Same as donor car</option>';
    
    if (!State.selectedPack || !State.selectedPack.cars) return;
    
    // Sort car names alphabetically
    const carIds = Object.keys(State.selectedPack.cars).sort();
    
    for (const carId of carIds) {
        const name = carId.replace(/_/g, ' ');
        donorSelect.innerHTML += `<option value="${carId}">${name}</option>`;
        engineSelect.innerHTML += `<option value="${carId}">${name}</option>`;
    }
}

function findBestMatch() {
    const original = State.originalCar.metadata;
    let bestMatch = null;
    let bestScore = Infinity;
    
    for (const [carId, carData] of Object.entries(State.selectedPack.cars)) {
        const donor = carData.metadata;
        
        // Calculate distance score
        const massDiff = Math.abs((original.mass || 0) - (donor.mass || 0)) / (original.mass || 1);
        const wheelbaseDiff = Math.abs((original.wheelbase || 0) - (donor.wheelbase || 0)) / (original.wheelbase || 1);
        
        const origTrackAvg = ((original.trackFront || 0) + (original.trackRear || 0)) / 2;
        const donorTrackAvg = ((donor.trackFront || 0) + (donor.trackRear || 0)) / 2;
        const trackDiff = Math.abs(origTrackAvg - donorTrackAvg) / (origTrackAvg || 1);
        
        const score = massDiff + wheelbaseDiff + trackDiff;
        
        if (score < bestScore) {
            bestScore = score;
            bestMatch = { carId, ...carData };
        }
    }
    
    State.matchedDonor = bestMatch;
    displayMatch(bestMatch, bestScore);
}

function displayMatch(donor, score) {
    // Match info removed from UI — data stays in State for swap
}

async function generateSwap() {
    const btn = document.getElementById('download-btn');
    btn.classList.remove('btn-pulse-active');
    btn.classList.add('flashing');
    btn.disabled = true;
    
    try {
        const zip = new JSZip();
        const donor = State.matchedDonor;
        const original = State.originalCar;
        
        // Check for engine source override
        const engineSelectVal = document.getElementById('engine-select').value;
        let engineSource = donor;
        if (engineSelectVal && State.selectedPack.cars[engineSelectVal]) {
            engineSource = { carId: engineSelectVal, ...State.selectedPack.cars[engineSelectVal] };
        }
        
        // Get visual adjustments
        const adj = getVisualAdjustments();
        
        // Swap car.ini
        const carIni = swapCarIni(original.files['car.ini'], donor.files['car.ini'], adj);
        zip.file('data/car.ini', carIni);
        
        // Swap suspensions.ini
        const suspIni = swapSuspensionsIni(original.files['suspensions.ini'], donor.files['suspensions.ini'], adj);
        zip.file('data/suspensions.ini', suspIni);
        
        // Swap tyres.ini
        const tyresIni = swapTyresIni(original.files['tyres.ini'], donor.files['tyres.ini']);
        zip.file('data/tyres.ini', tyresIni);
        
        // Engine files from engine source (may differ from donor)
        const engineFiles = ['engine.ini', 'drivetrain.ini'];
        for (const fileName of engineFiles) {
            if (engineSource.files[fileName]) {
                zip.file('data/' + fileName, engineSource.files[fileName]);
            }
        }
        // Engine .lut files (power.lut, engine_map*.lut etc) from engine source
        for (const [fileName, content] of Object.entries(engineSource.files)) {
            if (fileName.endsWith('.lut') && (fileName.startsWith('power') || fileName.startsWith('engine') || fileName.startsWith('throttle'))) {
                zip.file('data/' + fileName, content);
            }
        }
        
        // Copy remaining physics files from donor
        const otherPhysics = ['brakes.ini', 'electronics.ini', 'aero.ini', 'setup.ini', 
                              'damage.ini', 'drs.ini', 'escmode.ini'];
        for (const fileName of otherPhysics) {
            if (donor.files[fileName]) {
                zip.file('data/' + fileName, donor.files[fileName]);
            }
        }
        
        // Copy remaining .lut and .rto files from donor (skip engine ones already added)
        for (const [fileName, content] of Object.entries(donor.files)) {
            if ((fileName.endsWith('.lut') || fileName.endsWith('.rto')) && !zip.files['data/' + fileName]) {
                zip.file('data/' + fileName, content);
            }
        }
        
        // Store generated files for tuner correction
        State.lastGenFiles = {};
        zip.forEach(function(relativePath, file) {
            // We'll re-read them from the zip
        });
        // Simpler: store the string content directly
        State.lastGenFiles = { 'car.ini': carIni, 'suspensions.ini': suspIni, 'tyres.ini': tyresIni };
        // Store other files too
        for (const [fn, content] of Object.entries(donor.files)) {
            if (!State.lastGenFiles[fn]) State.lastGenFiles[fn] = content;
        }
        if (engineSource !== donor) {
            for (const [fn, content] of Object.entries(engineSource.files)) {
                if (fn === 'engine.ini' || fn === 'drivetrain.ini' || (fn.endsWith('.lut') && (fn.startsWith('power') || fn.startsWith('engine') || fn.startsWith('throttle')))) {
                    State.lastGenFiles[fn] = content;
                }
            }
        }

        // Generate and download
        const blob = await zip.generateAsync({ type: 'blob' });
        const packName = State.selectedPack.packName.replace(/ /g, '_');
        
        // Show interstitial modal BEFORE download
        btn.classList.remove('flashing');
        btn.disabled = false;
        if (!checkPatreonSession()) markTrialUsed();
        showDownloadModal(blob, `data_${packName}.zip`);
        
    } catch (error) {
        console.error('Swap generation error:', error);
        alert('Error generating swap. Please try again.');
        btn.classList.remove('flashing');
        btn.disabled = false;
    }
}

function swapCarIni(originalContent, donorContent, adj) {
    const original = INIParser.parse(originalContent);
    const donor = INIParser.parse(donorContent);
    
    // Start with deep copy of donor — donor is the base for everything
    const result = JSON.parse(JSON.stringify(donor));
    
    // Override HEADER from original (unless BDC which needs extended-2)
    if (State.selectedPack.packName !== 'BDC' && State.selectedPack.packName !== 'BDC v6' && original.HEADER) {
        result.HEADER = { ...original.HEADER };
    }
    
    // Keep original INFO (car name etc)
    if (original.INFO) result.INFO = { ...original.INFO };
    
    // BASIC: donor base, override only geometry-dependent values from original
    if (original.BASIC) {
        if (original.BASIC.INERTIA) result.BASIC.INERTIA = original.BASIC.INERTIA;
        if (original.BASIC.GRAPHICS_OFFSET) {
            // Keep original X,Z but donor Y (height) + height adjustment
            const origParts = original.BASIC.GRAPHICS_OFFSET.split(',').map(s => s.trim());
            const donorParts = (result.BASIC.GRAPHICS_OFFSET || '0,0,0').split(',').map(s => s.trim());
            if (origParts.length >= 3 && donorParts.length >= 3) {
                const finalY = (parseFloat(donorParts[1]) + (adj.height || 0)).toFixed(3);
                result.BASIC.GRAPHICS_OFFSET = `${origParts[0]}, ${finalY}, ${origParts[2]}`;
            } else {
                result.BASIC.GRAPHICS_OFFSET = original.BASIC.GRAPHICS_OFFSET;
            }
        }
        // Apply pitch adjustment
        const basePitch = parseFloat(original.BASIC.GRAPHICS_PITCH_ROTATION || '0');
        const finalPitch = (basePitch + (adj.pitch || 0)).toFixed(2);
        result.BASIC.GRAPHICS_PITCH_ROTATION = finalPitch;
    }
    
    // Keep original GRAPHICS and RIDE (visual/geometry dependent)
    if (original.GRAPHICS) result.GRAPHICS = { ...original.GRAPHICS };
    if (original.RIDE) result.RIDE = { ...original.RIDE };
    
    // FUELTANK: donor base, but keep original POSITION (physical location in the car body)
    if (original.FUELTANK && result.FUELTANK) {
        if (original.FUELTANK.POSITION) result.FUELTANK.POSITION = original.FUELTANK.POSITION;
    }
    
    // Everything else (CONTROLS, FUEL, PIT_STOP, etc) stays from donor
    
    return INIParser.serialize(result);
}

function swapSuspensionsIni(originalContent, donorContent, adj) {
    const original = INIParser.parse(originalContent);
    const donor = INIParser.parse(donorContent);
    
    // Deep copy donor as base
    const result = JSON.parse(JSON.stringify(donor));
    
    // Keep original wheelbase and CG
    if (original.BASIC) {
        if (!result.BASIC) result.BASIC = {};
        if (original.BASIC.WHEELBASE) result.BASIC.WHEELBASE = original.BASIC.WHEELBASE;
        if (original.BASIC.CG_LOCATION) result.BASIC.CG_LOCATION = original.BASIC.CG_LOCATION;
    }
    
    // Keep original TRACK values + apply width adjustments
    if (original.FRONT) {
        if (!result.FRONT) result.FRONT = {};
        const origFrontTrack = parseFloat(original.FRONT.TRACK || '1.5');
        result.FRONT.TRACK = (origFrontTrack + (adj.frontWidth || 0)).toFixed(4);
    }
    if (original.REAR) {
        if (!result.REAR) result.REAR = {};
        const origRearTrack = parseFloat(original.REAR.TRACK || '1.5');
        result.REAR.TRACK = (origRearTrack + (adj.rearWidth || 0)).toFixed(4);
    }
    
    // Keep original GRAPHICS_OFFSETS section entirely
    if (original.GRAPHICS_OFFSETS) {
        result.GRAPHICS_OFFSETS = { ...original.GRAPHICS_OFFSETS };
    }
    
    return INIParser.serialize(result);
}

function swapTyresIni(originalContent, donorContent) {
    const original = INIParser.parse(originalContent);
    const donor = INIParser.parse(donorContent);
    
    // Deep copy donor as base
    const result = JSON.parse(JSON.stringify(donor));
    
    // Keep original RADIUS and RIM_RADIUS in all FRONT*/REAR* sections
    for (const section of Object.keys(result)) {
        if (section.startsWith('FRONT') || section.startsWith('REAR')) {
            const origSection = section.includes('FRONT') ? 'FRONT' : 'REAR';
            if (original[origSection]) {
                if (original[origSection].RADIUS) result[section].RADIUS = original[origSection].RADIUS;
                if (original[origSection].RIM_RADIUS) result[section].RIM_RADIUS = original[origSection].RIM_RADIUS;
            }
        }
    }
    
    return INIParser.serialize(result);
}

function activateStep(stepId) {
    document.getElementById(stepId).classList.add('active');
}

function deactivateStep(stepId) {
    document.getElementById(stepId).classList.remove('active');
}

function showLoading(text = 'Loading...') {
    document.getElementById('loading-text').textContent = text;
    document.getElementById('loading-overlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.add('hidden');
}

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function showDownloadModal(blob, filename) {
    const packId = State.selectedPack.packName.replace(/ /g, '_');
    const logoExt = packId === 'NNTS' ? 'jpg' : 'png';
    const logoUrl = `logos/${packId}.${logoExt}`;

    const modal = document.createElement('div');
    modal.id = 'download-modal';
    modal.innerHTML = `
        <div class="dm-backdrop"></div>
        <div class="dm-card">
            <img src="realisimhq-logo.png" alt="RealiSimHQ" class="dm-site-logo">
            <div class="dm-logo-ring preparing">
                <img src="${logoUrl}" alt="${State.selectedPack.packName}" class="dm-pack-logo">
            </div>
            <h2 class="dm-title">Your ${State.selectedPack.packName} swap is ready</h2>
            <p class="dm-subtitle">${State.selectedPack.packName} &rarr; <span style="color:var(--accent-cyan)">${State.originalCar.metadata.name || 'your car'}</span></p>
            <div class="dm-divider"></div>
            <p class="dm-cta" style="font-size:1.1rem;">Thank you for your continued support! 🙏</p>
            <p style="color:var(--text-secondary);margin-top:8px;">Have fun out there. 🏎️💨</p>
        </div>
    `;
    document.body.appendChild(modal);

    // Click backdrop to close
    modal.querySelector('.dm-backdrop').addEventListener('click', closeDownloadModal);

    // After 5s: fire the download
    setTimeout(() => {
        const ring = modal.querySelector('.dm-logo-ring');
        ring.classList.remove('preparing');
        ring.classList.add('done');
        modal.querySelector('.dm-title').textContent = 'Starting download\u2026';

        // Small delay so they see the green ring before the file picker covers it
        setTimeout(() => {
            downloadBlob(blob, filename);
            // After download, add a close button that opens the tuner
            setTimeout(() => {
                modal.querySelector('.dm-title').textContent = 'Download started!';
                const closeDiv = document.createElement('div');
                closeDiv.style.marginTop = '20px';
                closeDiv.innerHTML = '<button class="dm-close" onclick="closeDownloadModal(); showTuner();">🔧 Open Visual Tuner</button>' +
                    '<br><button class="dm-close" style="margin-top:8px;opacity:0.5;" onclick="closeDownloadModal();">Close</button>';
                modal.querySelector('.dm-card').appendChild(closeDiv);
            }, 1000);
        }, 600);
    }, 5000);
}

function closeDownloadModal() {
    const modal = document.getElementById('download-modal');
    if (modal) {
        modal.classList.add('dm-fade-out');
        setTimeout(() => modal.remove(), 300);
    }
}

// ─── Visual Tuner ───
const Tuner = { h: 0, fw: 0, rw: 0, pitch: 0, locked: false, baseline: null };
// Store last generated files for correction
State.lastGenFiles = null;

const T_LIMIT = 0.750;
const T_PX_TRACK = 2.5;  // px per inch for track width
const T_PX_HEIGHT = 2.5; // px per inch for height

function tunerInches(val) {
    // reuse the toInches function
    return toInches(val);
}

function tunerAdj(key, delta) {
    if (key === 'pitch') {
        Tuner.pitch = Math.round(Tuner.pitch + delta);
        Tuner.pitch = Math.max(-20, Math.min(20, Tuner.pitch));
    } else {
        Tuner[key] = Math.round((Tuner[key] + delta) * 1e6) / 1e6;
        Tuner[key] = Math.max(-T_LIMIT, Math.min(T_LIMIT, Tuner[key]));
    }
    updateTunerUI();
}

function tunerReset(key) {
    Tuner[key] = 0;
    updateTunerUI();
}

function updateTunerUI() {
    // Value displays
    document.getElementById('tuner-fw-val').textContent = toInches(Tuner.fw);
    document.getElementById('tuner-rw-val').textContent = toInches(Tuner.rw);
    document.getElementById('tuner-h-val').textContent = toInches(Tuner.h);
    var psign = Tuner.pitch > 0 ? '+' : '';
    document.getElementById('tuner-pitch-val').textContent = psign + Tuner.pitch + '°';

    // Pitch knob rotation
    document.getElementById('tuner-pitch-line').setAttribute('transform', 'rotate(' + Tuner.pitch + ', 60, 60)');

    // Top-down: move tires
    var fPx = (Tuner.fw / 0.025) * T_PX_TRACK;
    var rPx = (Tuner.rw / 0.025) * T_PX_TRACK;
    document.getElementById('t-lf').setAttribute('transform', 'translate(' + (-fPx) + ',0)');
    document.getElementById('t-rf').setAttribute('transform', 'translate(' + fPx + ',0)');
    document.getElementById('t-lr').setAttribute('transform', 'translate(' + (-rPx) + ',0)');
    document.getElementById('t-rr').setAttribute('transform', 'translate(' + rPx + ',0)');

    // Side: height + pitch
    var hPx = (Tuner.h / 0.025) * T_PX_HEIGHT;
    document.getElementById('t-car-group').setAttribute('transform',
        'translate(0,' + (-hPx) + ') rotate(' + Tuner.pitch + ',260,170)');
}

function tunerToggleLock() {
    var btn = document.getElementById('tuner-lock-btn');
    var help = document.getElementById('tuner-help');
    if (!Tuner.locked) {
        // Lock: store baseline, reset to 0
        Tuner.baseline = { h: Tuner.h, fw: Tuner.fw, rw: Tuner.rw, pitch: Tuner.pitch };
        Tuner.h = 0; Tuner.fw = 0; Tuner.rw = 0; Tuner.pitch = 0;
        Tuner.locked = true;
        btn.textContent = '🔒 LOCKED — Click to Unlock';
        btn.style.borderColor = '#10b981';
        btn.style.color = '#10b981';
        btn.style.background = 'rgba(16,185,129,0.08)';
        help.innerHTML = 'Now adjust to where you <strong style="color:#4ade80;">WANT</strong> the car to be.';
        document.getElementById('tuner-gen-wrap').classList.remove('hidden');
        updateTunerUI();
    } else {
        // Unlock: restore baseline values
        Tuner.h = Tuner.baseline.h;
        Tuner.fw = Tuner.baseline.fw;
        Tuner.rw = Tuner.baseline.rw;
        Tuner.pitch = Tuner.baseline.pitch;
        Tuner.baseline = null;
        Tuner.locked = false;
        btn.textContent = '🔓 LOCK ZERO POINT';
        btn.style.borderColor = '#fbbf24';
        btn.style.color = '#fbbf24';
        btn.style.background = 'rgba(251,191,36,0.08)';
        help.innerHTML = 'Adjust to match how your car looks in-game, then <strong style="color:#fbbf24;">LOCK</strong> your zero point.';
        document.getElementById('tuner-gen-wrap').classList.add('hidden');
        updateTunerUI();
    }
}

var _tunerPitchDragging = false;
function tunerPitchDrag(e) {
    e.preventDefault();
    _tunerPitchDragging = true;
    var knob = document.getElementById('tuner-pitch-knob');
    var rect = knob.getBoundingClientRect();
    var cx = rect.left + rect.width / 2;
    var cy = rect.top + rect.height / 2;
    function onMove(ev) {
        if (!_tunerPitchDragging) return;
        var pt = ev.touches ? ev.touches[0] : ev;
        var dx = pt.clientX - cx;
        var dy = pt.clientY - cy;
        var angle = Math.atan2(dy, dx) * (180 / Math.PI);
        Tuner.pitch = Math.round(Math.max(-20, Math.min(20, angle)));
        updateTunerUI();
    }
    function onUp() {
        _tunerPitchDragging = false;
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        document.removeEventListener('touchmove', onMove);
        document.removeEventListener('touchend', onUp);
    }
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    document.addEventListener('touchmove', onMove);
    document.addEventListener('touchend', onUp);
}

function showTuner() {
    // Reset tuner state
    Tuner.h = 0; Tuner.fw = 0; Tuner.rw = 0; Tuner.pitch = 0;
    Tuner.locked = false; Tuner.baseline = null;
    var btn = document.getElementById('tuner-lock-btn');
    btn.textContent = '🔓 LOCK ZERO POINT';
    btn.style.borderColor = '#fbbf24';
    btn.style.color = '#fbbf24';
    btn.style.background = 'rgba(251,191,36,0.08)';
    document.getElementById('tuner-help').innerHTML = 'Adjust to match how your car looks in-game, then <strong style="color:#fbbf24;">LOCK</strong> your zero point.';
    document.getElementById('tuner-gen-wrap').classList.add('hidden');
    updateTunerUI();

    var section = document.getElementById('tuner-section');
    section.classList.remove('hidden');
    section.classList.add('active');
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function generateCorrection() {
    if (!State.lastGenFiles || !Tuner.locked) return;

    var genBtn = document.getElementById('tuner-gen-btn');
    genBtn.disabled = true;
    genBtn.textContent = 'Generating...';

    try {
        var zip = new JSZip();
        // The correction = post-lock adjustment values
        var corrHeight = Tuner.h;
        var corrFrontWidth = Tuner.fw;
        var corrRearWidth = Tuner.rw;
        var corrPitch = Tuner.pitch * -0.10; // degrees to raw

        // Fix car.ini
        var carData = INIParser.parse(State.lastGenFiles['car.ini']);
        if (carData.BASIC) {
            // Adjust GRAPHICS_OFFSET Y
            var parts = (carData.BASIC.GRAPHICS_OFFSET || '0,0,0').split(',').map(function(s) { return s.trim(); });
            if (parts.length >= 3) {
                parts[1] = (parseFloat(parts[1]) + corrHeight).toFixed(3);
                carData.BASIC.GRAPHICS_OFFSET = parts.join(', ');
            }
            // Adjust pitch
            var currentPitch = parseFloat(carData.BASIC.GRAPHICS_PITCH_ROTATION || '0');
            carData.BASIC.GRAPHICS_PITCH_ROTATION = (currentPitch + corrPitch).toFixed(2);
        }
        zip.file('data/car.ini', INIParser.serialize(carData));

        // Fix suspensions.ini
        var suspData = INIParser.parse(State.lastGenFiles['suspensions.ini']);
        if (suspData.FRONT) {
            var ft = parseFloat(suspData.FRONT.TRACK || '1.5');
            suspData.FRONT.TRACK = (ft + corrFrontWidth).toFixed(4);
        }
        if (suspData.REAR) {
            var rt = parseFloat(suspData.REAR.TRACK || '1.5');
            suspData.REAR.TRACK = (rt + corrRearWidth).toFixed(4);
        }
        zip.file('data/suspensions.ini', INIParser.serialize(suspData));

        // Copy all other files as-is
        for (var fname in State.lastGenFiles) {
            if (fname !== 'car.ini' && fname !== 'suspensions.ini') {
                zip.file('data/' + fname, State.lastGenFiles[fname]);
            }
        }

        var blob = await zip.generateAsync({ type: 'blob' });
        var packName = State.selectedPack ? State.selectedPack.packName.replace(/ /g, '_') : 'corrected';
        downloadBlob(blob, 'data_' + packName + '_corrected.zip');

        if (!checkPatreonSession()) markTrialUsed();
    } catch (err) {
        console.error('Correction generation error:', err);
        alert('Error generating correction: ' + err.message);
    } finally {
        genBtn.disabled = false;
        genBtn.innerHTML = '<svg class="btn-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg> Generate Corrected Physics';
    }
}

// ─── Visual Adjustments ───
let _adjHeight = 0;
let _adjFrontWidth = 0;
let _adjRearWidth = 0;
let _pitchDegrees = 0;
const ADJ_LIMIT = 0.750;

function toInches(val) {
    var inches = val / 0.02500;
    var neg = inches < 0;
    var abs = Math.abs(inches);
    var whole = Math.floor(abs);
    var eighths = Math.round((abs - whole) * 8);
    if (eighths === 8) { whole++; eighths = 0; }
    var num = eighths, den = 8;
    if (num > 0) {
        if (num % 4 === 0) { num /= 4; den /= 4; }
        else if (num % 2 === 0) { num /= 2; den /= 2; }
    }
    var sign = neg ? '-' : '';
    if (whole === 0 && num === 0) return '0"';
    if (num === 0) return sign + whole + '"';
    if (whole === 0) return sign + num + '/' + den + '"';
    return sign + whole + ' ' + num + '/' + den + '"';
}

function adjHeight(delta) {
    _adjHeight = Math.round((_adjHeight + delta) * 1e6) / 1e6;
    _adjHeight = Math.max(-ADJ_LIMIT, Math.min(ADJ_LIMIT, _adjHeight));
    document.getElementById('adj-height-val').textContent = toInches(_adjHeight);
}
function resetHeight() { _adjHeight = 0; document.getElementById('adj-height-val').textContent = '0"'; }

function adjFrontWidth(delta) {
    _adjFrontWidth = Math.round((_adjFrontWidth + delta) * 1e6) / 1e6;
    _adjFrontWidth = Math.max(-ADJ_LIMIT, Math.min(ADJ_LIMIT, _adjFrontWidth));
    document.getElementById('adj-fwidth-val').textContent = toInches(_adjFrontWidth);
}
function resetFrontWidth() { _adjFrontWidth = 0; document.getElementById('adj-fwidth-val').textContent = '0"'; }

function adjRearWidth(delta) {
    _adjRearWidth = Math.round((_adjRearWidth + delta) * 1e6) / 1e6;
    _adjRearWidth = Math.max(-ADJ_LIMIT, Math.min(ADJ_LIMIT, _adjRearWidth));
    document.getElementById('adj-rwidth-val').textContent = toInches(_adjRearWidth);
}
function resetRearWidth() { _adjRearWidth = 0; document.getElementById('adj-rwidth-val').textContent = '0"'; }

function updatePitchUI() {
    var sign = _pitchDegrees > 0 ? '+' : '';
    document.getElementById('adj-pitch-val').textContent = sign + _pitchDegrees + '°';
    var angle = _pitchDegrees;
    document.getElementById('pitch-line').setAttribute('transform', 'rotate(' + angle + ', 60, 60)');
}

function adjPitch(delta) {
    _pitchDegrees = Math.round(_pitchDegrees + delta);
    _pitchDegrees = Math.max(-20, Math.min(20, _pitchDegrees));
    updatePitchUI();
}

function resetPitch() {
    _pitchDegrees = 0;
    updatePitchUI();
}

var _pitchDragging = false;
function startPitchDrag(e) {
    e.preventDefault();
    _pitchDragging = true;
    var knob = document.getElementById('pitch-knob');
    var rect = knob.getBoundingClientRect();
    var cx = rect.left + rect.width / 2;
    var cy = rect.top + rect.height / 2;

    function onMove(ev) {
        if (!_pitchDragging) return;
        var pt = ev.touches ? ev.touches[0] : ev;
        var dx = pt.clientX - cx;
        var dy = pt.clientY - cy;
        var angle = Math.atan2(dy, dx) * (180 / Math.PI);
        _pitchDegrees = Math.round(Math.max(-20, Math.min(20, angle)));
        updatePitchUI();
    }
    function onUp() {
        _pitchDragging = false;
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        document.removeEventListener('touchmove', onMove);
        document.removeEventListener('touchend', onUp);
    }
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    document.addEventListener('touchmove', onMove);
    document.addEventListener('touchend', onUp);
}

function getVisualAdjustments() {
    return {
        height: _adjHeight,
        pitch: _pitchDegrees * -0.10,
        frontWidth: _adjFrontWidth,
        rearWidth: _adjRearWidth
    };
}

function initVisualToggle() {
    var toggle = document.getElementById('visual-toggle');
    if (toggle) {
        toggle.addEventListener('click', function() {
            document.getElementById('visual-body').classList.toggle('hidden');
            document.getElementById('visual-arrow').classList.toggle('open');
        });
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => { init(); initPatreonGate(); initVisualToggle(); });
