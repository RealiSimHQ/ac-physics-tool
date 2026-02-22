// AC Physics Swapper - Client-side app
// RealiSimHQ 2026

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
    activateStep('pack-section');
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
    activateStep('pack-section');
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
        
        activateStep('advanced-section');
        activateStep('download-section');
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
        
        // Swap car.ini
        const carIni = swapCarIni(original.files['car.ini'], donor.files['car.ini']);
        zip.file('data/car.ini', carIni);
        
        // Swap suspensions.ini
        const suspIni = swapSuspensionsIni(original.files['suspensions.ini'], donor.files['suspensions.ini']);
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
        
        // Generate and download
        const blob = await zip.generateAsync({ type: 'blob' });
        const packName = State.selectedPack.packName.replace(/ /g, '_');
        
        // Show interstitial modal BEFORE download
        btn.classList.remove('flashing');
        btn.disabled = false;
        showDownloadModal(blob, `data_${packName}.zip`);
        
    } catch (error) {
        console.error('Swap generation error:', error);
        alert('Error generating swap. Please try again.');
        btn.classList.remove('flashing');
        btn.disabled = false;
    }
}

function swapCarIni(originalContent, donorContent) {
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
            // Keep original X,Z but donor Y (height)
            const origParts = original.BASIC.GRAPHICS_OFFSET.split(',').map(s => s.trim());
            const donorParts = (result.BASIC.GRAPHICS_OFFSET || '0,0,0').split(',').map(s => s.trim());
            if (origParts.length >= 3 && donorParts.length >= 3) {
                result.BASIC.GRAPHICS_OFFSET = `${origParts[0]}, ${donorParts[1]}, ${origParts[2]}`;
            } else {
                result.BASIC.GRAPHICS_OFFSET = original.BASIC.GRAPHICS_OFFSET;
            }
        }
        if (original.BASIC.GRAPHICS_PITCH_ROTATION) result.BASIC.GRAPHICS_PITCH_ROTATION = original.BASIC.GRAPHICS_PITCH_ROTATION;
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

function swapSuspensionsIni(originalContent, donorContent) {
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
    
    // ONLY keep original TRACK — all geometry comes from donor pack
    const keepKeys = ['TRACK'];
    
    for (const section of ['FRONT', 'REAR']) {
        if (original[section]) {
            if (!result[section]) result[section] = {};
            for (const key of keepKeys) {
                if (original[section][key] !== undefined) {
                    result[section][key] = original[section][key];
                }
            }
        }
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
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active');
    });
    document.getElementById(stepId).classList.add('active');
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
            <div class="dm-logo-ring preparing">
                <img src="${logoUrl}" alt="${State.selectedPack.packName}" class="dm-pack-logo">
            </div>
            <h2 class="dm-title">Your ${State.selectedPack.packName} swap is ready</h2>
            <p class="dm-subtitle">${State.selectedPack.packName} &rarr; <span style="color:var(--accent-cyan)">${State.originalCar.metadata.name || 'your car'}</span></p>
            <div class="dm-divider"></div>
            <p class="dm-cta">If this saved you time, consider giving back.</p>
            <div class="dm-links">
                <a href="https://www.patreon.com/RealiSimHQ" target="_blank" class="support-btn patreon-btn">Support on Patreon</a>
                <a href="https://paypal.me/PodcastPrimates" target="_blank" class="support-btn tip-btn">Leave a Tip</a>
            </div>
            <p style="font-size:0.85rem;color:var(--text-secondary);opacity:0.5;margin-top:12px;">100% of tips go toward building more tools for the community</p>
        </div>
    `;
    document.body.appendChild(modal);

    // After 5s: fire the download, then close modal
    setTimeout(() => {
        const ring = modal.querySelector('.dm-logo-ring');
        ring.classList.remove('preparing');
        ring.classList.add('done');
        modal.querySelector('.dm-title').textContent = 'Starting download\u2026';

        // Small delay so they see the green ring before the file picker covers it
        setTimeout(() => {
            downloadBlob(blob, filename);
            closeDownloadModal();
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

// Initialize on load
document.addEventListener('DOMContentLoaded', init);
