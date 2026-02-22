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
        
        // Find best match
        findBestMatch();
        
        activateStep('download-section');
    } catch (error) {
        console.error('Failed to load pack:', error);
        alert('Failed to load carpack data.');
    } finally {
        hideLoading();
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
    
    // Show celebration overlay with pack logo
    const overlay = document.getElementById('download-overlay');
    const packLogo = document.getElementById('download-pack-logo');
    const dlText = overlay.querySelector('.download-text');
    
    if (State.selectedPack) {
        packLogo.src = `logos/${State.selectedPack.logo}`;
        packLogo.alt = State.selectedPack.packName;
    }
    dlText.textContent = 'Generating physics swap...';
    overlay.classList.remove('hidden');
    
    try {
        const zip = new JSZip();
        const donor = State.matchedDonor;
        const original = State.originalCar;
        
        // Swap car.ini
        const carIni = swapCarIni(original.files['car.ini'], donor.files['car.ini']);
        zip.file('car.ini', carIni);
        
        // Swap suspensions.ini
        const suspIni = swapSuspensionsIni(original.files['suspensions.ini'], donor.files['suspensions.ini']);
        zip.file('suspensions.ini', suspIni);
        
        // Swap tyres.ini
        const tyresIni = swapTyresIni(original.files['tyres.ini'], donor.files['tyres.ini']);
        zip.file('tyres.ini', tyresIni);
        
        // Copy all other physics files from donor
        const physicsFiles = ['engine.ini', 'drivetrain.ini', 'brakes.ini', 'electronics.ini', 
                             'aero.ini', 'setup.ini', 'damage.ini', 'drs.ini', 'escmode.ini'];
        
        for (const fileName of physicsFiles) {
            if (donor.files[fileName]) {
                zip.file(fileName, donor.files[fileName]);
            }
        }
        
        // Copy all .lut and .rto files from donor
        for (const [fileName, content] of Object.entries(donor.files)) {
            if (fileName.endsWith('.lut') || fileName.endsWith('.rto')) {
                zip.file(fileName, content);
            }
        }
        
        // Generate and download
        const blob = await zip.generateAsync({ type: 'blob' });
        const packName = State.selectedPack.packName.replace(/ /g, '_');
        
        dlText.textContent = 'Download complete!';
        downloadBlob(blob, `data_${packName}.zip`);
        
        // Keep celebration visible for 2.5s then fade out
        setTimeout(() => {
            overlay.classList.add('hidden');
            btn.classList.remove('flashing');
            btn.disabled = false;
        }, 2500);
        
    } catch (error) {
        console.error('Swap generation error:', error);
        alert('Error generating swap. Please try again.');
        overlay.classList.add('hidden');
        btn.classList.remove('flashing');
        btn.disabled = false;
    }
}

function swapCarIni(originalContent, donorContent) {
    const original = INIParser.parse(originalContent);
    const donor = INIParser.parse(donorContent);
    
    const result = {};
    
    // Keep original header (unless BDC)
    if (State.selectedPack.packName === 'BDC' && donor.HEADER) {
        result.HEADER = donor.HEADER;
    } else if (original.HEADER) {
        result.HEADER = original.HEADER;
    }
    
    // Keep original INFO
    if (original.INFO) result.INFO = original.INFO;
    
    // BASIC: keep mass, inertia, graphics from original
    result.BASIC = { ...donor.BASIC };
    if (original.BASIC) {
        if (original.BASIC.TOTALMASS) result.BASIC.TOTALMASS = original.BASIC.TOTALMASS;
        if (original.BASIC.INERTIA) result.BASIC.INERTIA = original.BASIC.INERTIA;
        if (original.BASIC.GRAPHICS_OFFSET) result.BASIC.GRAPHICS_OFFSET = original.BASIC.GRAPHICS_OFFSET;
        if (original.BASIC.GRAPHICS_PITCH_ROTATION) result.BASIC.GRAPHICS_PITCH_ROTATION = original.BASIC.GRAPHICS_PITCH_ROTATION;
    }
    
    // Keep original GRAPHICS and RIDE
    if (original.GRAPHICS) result.GRAPHICS = original.GRAPHICS;
    if (original.RIDE) result.RIDE = original.RIDE;
    
    // CONTROLS: use donor as base but keep original STEER_LOCK and STEER_RATIO
    // since original steer geometry (WBCAR_STEER/WBTYRE_STEER) is preserved
    if (donor.CONTROLS) {
        result.CONTROLS = { ...donor.CONTROLS };
        if (original.CONTROLS) {
            if (original.CONTROLS.STEER_LOCK !== undefined) result.CONTROLS.STEER_LOCK = original.CONTROLS.STEER_LOCK;
            if (original.CONTROLS.STEER_RATIO !== undefined) result.CONTROLS.STEER_RATIO = original.CONTROLS.STEER_RATIO;
            if (original.CONTROLS.LINEAR_STEER_ROD_RATIO !== undefined) result.CONTROLS.LINEAR_STEER_ROD_RATIO = original.CONTROLS.LINEAR_STEER_ROD_RATIO;
        }
    } else if (original.CONTROLS) {
        result.CONTROLS = original.CONTROLS;
    }
    if (donor.FUEL) result.FUEL = donor.FUEL;
    if (donor.FUELTANK) result.FUELTANK = donor.FUELTANK;
    if (donor.PIT_STOP) result.PIT_STOP = donor.PIT_STOP;
    
    return INIParser.serialize(result);
}

function swapSuspensionsIni(originalContent, donorContent) {
    const original = INIParser.parse(originalContent);
    const donor = INIParser.parse(donorContent);
    
    const result = { ...donor };
    
    // Keep original wheelbase and CG
    if (original.BASIC) {
        if (!result.BASIC) result.BASIC = {};
        if (original.BASIC.WHEELBASE) result.BASIC.WHEELBASE = original.BASIC.WHEELBASE;
        if (original.BASIC.CG_LOCATION) result.BASIC.CG_LOCATION = original.BASIC.CG_LOCATION;
    }
    
    // Keep original TRACK and geometry
    const keepKeys = ['TRACK', 'WBCAR_TOP_FRONT', 'WBCAR_TOP_REAR', 'WBCAR_BOTTOM_FRONT', 
                      'WBCAR_BOTTOM_REAR', 'WBTYRE_TOP', 'WBTYRE_BOTTOM', 'WBCAR_STEER', 
                      'WBTYRE_STEER', 'BASEY', 'RIM_OFFSET', 'HUB_MASS'];
    
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
    
    const result = { ...donor };
    
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

// Initialize on load
document.addEventListener('DOMContentLoaded', init);
