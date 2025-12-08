// Measurement system toggle
let measurementSystem = 'metric'; // Default

const metricBtn = document.getElementById('metricBtn');
const imperialBtn = document.getElementById('imperialBtn');
const heightLabel = document.getElementById('heightLabel');
const weightLabel = document.getElementById('weightLabel');
const heightInput = document.getElementById('height');
const weightInput = document.getElementById('weight');

metricBtn.addEventListener('click', function() {
    measurementSystem = 'metric';
    metricBtn.classList.add('bg-blue-600', 'text-white');
    metricBtn.classList.remove('text-slate-600', 'hover:bg-slate-200');
    imperialBtn.classList.remove('bg-blue-600', 'text-white');
    imperialBtn.classList.add('text-slate-600', 'hover:bg-slate-200');
    
    heightLabel.textContent = 'Height (cm)';
    weightLabel.textContent = 'Weight (kg)';
    heightInput.placeholder = 'e.g. 175';
    weightInput.placeholder = 'e.g. 70';
    heightInput.min = '100';
    heightInput.max = '250';
    weightInput.min = '30';
    weightInput.max = '300';
});

imperialBtn.addEventListener('click', function() {
    measurementSystem = 'imperial';
    imperialBtn.classList.add('bg-blue-600', 'text-white');
    imperialBtn.classList.remove('text-slate-600', 'hover:bg-slate-200');
    metricBtn.classList.remove('bg-blue-600', 'text-white');
    metricBtn.classList.add('text-slate-600', 'hover:bg-slate-200');
    
    heightLabel.textContent = 'Height (inches)';
    weightLabel.textContent = 'Weight (lbs)';
    heightInput.placeholder = 'e.g. 69';
    weightInput.placeholder = 'e.g. 154';
    heightInput.min = '40';
    heightInput.max = '100';
    weightInput.min = '66';
    weightInput.max = '660';
});

// Cycling checkbox toggle
const hasCyclingCheckbox = document.getElementById('hasCycling');
const cyclingDetails = document.getElementById('cyclingDetails');

hasCyclingCheckbox.addEventListener('change', function() {
    if (this.checked) {
        cyclingDetails.classList.remove('hidden');
    } else {
        cyclingDetails.classList.add('hidden');
        // Clear cycling inputs when unchecked
        document.getElementById('cyclingRides').value = '';
    }
});

document.getElementById('fitnessForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    // 1. UI State: Show Loading
    const btn = document.getElementById('generateBtn');
    const loading = document.getElementById('loading');
    const resultCard = document.getElementById('resultCard');
    const inputCard = document.getElementById('inputCard');

    btn.disabled = true;
    btn.classList.add('opacity-50', 'cursor-not-allowed'); // Tailwind disable styles
    
    inputCard.classList.add('hidden'); // Tailwind hide
    loading.classList.remove('hidden'); // Tailwind show

    // 2. Gather Data
    const formData = {
        days_available: parseInt(document.getElementById('days').value),
        experience_years: parseInt(document.getElementById('experience').value),
        goal: document.getElementById('goal').value,
        age: parseInt(document.getElementById('age').value),
        gender: document.getElementById('gender').value,
        height: parseFloat(document.getElementById('height').value),
        weight: parseFloat(document.getElementById('weight').value),
        environment: document.getElementById('environment').value,
        measurement_system: measurementSystem
    };

    // Add cycling data if checkbox is checked
    const hasCycling = document.getElementById('hasCycling').checked;
    if (hasCycling) {
        const cyclingRides = document.getElementById('cyclingRides').value;
        formData.cycling = {
            enabled: true,
            rides_per_year: cyclingRides ? parseInt(cyclingRides) : 0,
            season: "April - November"
        };
    } else {
        formData.cycling = {
            enabled: false
        };
    }

    // Add current routine if provided
    const currentRoutine = document.getElementById('currentRoutine').value.trim();
    if (currentRoutine) {
        formData.current_routine = currentRoutine;
    }

    try {
        const API_URL = window.location.hostname === 'localhost' 
            ? 'http://localhost:8080/generate' 
            : 'https://smart-coach-service-277077304112.us-central1.run.app/generate';
            
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        // 4. Render Result
        if (data.error) {
            alert("Error: " + data.error);
            location.reload();
            return;
        }

        // Update Badge
        document.getElementById('splitBadge').textContent = data.split;
        // Update Duration
        document.getElementById('durationText').textContent = data.duration;
        // Update Reasoning
        document.getElementById('confidenceText').textContent = data.confidence + "%";
        
        const badgesContainer = document.getElementById('reasoningBadges');
        badgesContainer.innerHTML = ''; // Clear previous
        
        if(data.reasoning) {
            data.reasoning.forEach(reason => {
                const badge = `<span class="bg-white text-blue-700 border border-blue-200 px-2 py-1 rounded text-xs font-semibold shadow-sm">${reason}</span>`;
                badgesContainer.innerHTML += badge;
            });
        }
        // Parse Markdown to HTML and enhance with structured exercise layout
        let planHTML = marked.parse(data.plan);
        planHTML = enhanceWorkoutDisplay(planHTML);
        document.getElementById('planContent').innerHTML = planHTML;

        // UI State: Show Result
        loading.classList.add('hidden');
        resultCard.classList.remove('hidden');

    } catch (error) {
        console.error(error);
        alert("Failed to connect to the Smart Coach Brain!");
        location.reload();
    }
});

// Function to enhance workout display with structured layout
function enhanceWorkoutDisplay(htmlContent) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlContent, 'text/html');
    
    // Find all list items (exercises)
    const listItems = doc.querySelectorAll('li');
    
    listItems.forEach(li => {
        const text = li.innerHTML;
        
        // Check if this is an exercise line (contains strong/bold tags)
        const strongTags = li.querySelectorAll('strong, b');
        
        if (strongTags.length > 0) {
            // Get exercise name from first strong tag
            const exerciseName = strongTags[0].textContent.trim();
            
            // Look for any YouTube link
            const linkElement = li.querySelector('a[href*="youtube.com"]');
            let videoId = null;
            
            if (linkElement) {
                const href = linkElement.getAttribute('href');
                const match = href.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]+)/);
                if (match) {
                    videoId = match[1];
                }
            }
            
            // Get exercise details (everything after the exercise name, excluding the video link)
            let details = text
                .replace(/<strong>.*?<\/strong>/gi, '')
                .replace(/<b>.*?<\/b>/gi, '')
                .replace(/<a[^>]*>.*?<\/a>/gi, '')
                .replace(/[-–—]\s*$/, '')
                .trim();
            
            // Remove leading dash if present
            details = details.replace(/^[-–—]\s*/, '').trim();
            
            // Create structured HTML
            let structuredHTML = `
                <div class="exercise-row">
                    <div class="exercise-info">
                        <span class="exercise-name">${exerciseName}</span>
                        <span class="exercise-details">${details}</span>
                    </div>
            `;
            
            // Add video thumbnail if available
            if (videoId) {
                const thumbnailUrl = `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`;
                structuredHTML += `
                    <div class="exercise-video">
                        <a href="https://youtube.com/watch?v=${videoId}" target="_blank" class="video-link">
                            <img src="${thumbnailUrl}" alt="${exerciseName} Demo" class="video-thumbnail">
                            <div class="play-overlay">▶</div>
                        </a>
                    </div>
                `;
            }
            
            structuredHTML += `</div>`;
            li.innerHTML = structuredHTML;
            li.classList.add('exercise-item');
        }
    });
    
    return doc.body.innerHTML;
}