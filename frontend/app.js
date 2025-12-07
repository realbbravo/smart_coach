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

    try {
        const API_URL = window.location.hostname === 'localhost' 
            ? 'http://localhost:8080/generate' 
            : '/generate';
            
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
        // Parse Markdown to HTML
        document.getElementById('planContent').innerHTML = marked.parse(data.plan);

        // UI State: Show Result
        loading.classList.add('hidden');
        resultCard.classList.remove('hidden');

    } catch (error) {
        console.error(error);
        alert("Failed to connect to the Smart Coach Brain!");
        location.reload();
    }
});