document.addEventListener('DOMContentLoaded', () => {
    // --- LANGKAH PENTING ---
    // Ganti URL di bawah ini dengan URL Cloudflare Worker Anda sendiri!
    const BACKEND_URL = 'https://youtube-analyzer-worker.hellomasketer.workers.dev';
    // ---------------------

    let youtubeData = null;

    // Elemen UI Utama
    const fetchBtn = document.getElementById('fetchBtn');
    const channelIdInput = document.getElementById('channelIdInput');
    const mainLoader = document.getElementById('mainLoader');
    const resultsPanel = document.getElementById('resultsPanel');
    const channelNameEl = document.getElementById('channelName');
    const subscriberCountEl = document.getElementById('subscriberCount');

    // Tombol dan Wadah Analisis (tidak berubah)
    const analyzeGeneralBtn = document.getElementById('analyzeGeneralBtn');
    const analyzeThumbnailsBtn = document.getElementById('analyzeThumbnailsBtn');
    const analyzeCommentsBtn = document.getElementById('analyzeCommentsBtn');
    const analyzeTitlesBtn = document.getElementById('analyzeTitlesBtn');
    const generalResultDiv = document.getElementById('general-result');
    const thumbnailResultDiv = document.getElementById('thumbnail-result');
    const commentResultDiv = document.getElementById('comment-result');
    const titleSuggestionResultDiv = document.getElementById('title-suggestion-result');

    const showSpinner = (element) => {
        element.innerHTML = '<div class="text-center p-8"><div class="animate-spin rounded-full h-10 w-10 border-b-2 border-slate-400 mx-auto"></div></div>';
    };

    const displayResult = (element, content) => {
        element.innerHTML = `<div class="bg-white p-6 rounded-xl shadow-md prose max-w-none">${marked.parse(content)}</div>`;
    };

    fetchBtn.addEventListener('click', async () => {
        const channelId = channelIdInput.value.trim();
        if (!channelId) { alert('Silakan masukkan Channel ID.'); return; }
        mainLoader.style.display = 'block';
        resultsPanel.classList.add('d-none');
        try {
            // Menggunakan BACKEND_URL untuk fetch data awal
            const response = await fetch(`${BACKEND_URL}/fetch-youtube-data`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ channel_id: channelId }),
            });
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || 'Gagal mengambil data channel.');
            }
            youtubeData = await response.json();
            channelNameEl.textContent = youtubeData.channel_name;
            subscriberCountEl.textContent = `${new Intl.NumberFormat().format(youtubeData.subscriber_count)} subscribers`;
            resultsPanel.classList.remove('d-none');
            [analyzeGeneralBtn, analyzeThumbnailsBtn, analyzeCommentsBtn, analyzeTitlesBtn].forEach(btn => {
                btn.disabled = false;
                btn.classList.remove('opacity-50', 'cursor-not-allowed');
            });
            [generalResultDiv, thumbnailResultDiv, commentResultDiv, titleSuggestionResultDiv].forEach(div => div.innerHTML = '');
        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            mainLoader.style.display = 'none';
        }
    });

    const handleAnalysisClick = async (btn, resultDiv, endpoint, payload) => {
        showSpinner(resultDiv);
        btn.disabled = true;
        btn.classList.add('opacity-50', 'cursor-not-allowed');
        try {
            // Menggunakan BACKEND_URL untuk semua fetch analisis
            const response = await fetch(`${BACKEND_URL}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const result = await response.json();
            displayResult(resultDiv, result.analysis);
        } catch (error) {
            resultDiv.innerHTML = `<div class="bg-red-100 text-red-700 p-4 rounded-lg">Gagal memuat analisis: ${error.message}</div>`;
        }
    };
    
    // Panggilan ke handleAnalysisClick sekarang menggunakan path endpoint saja
    analyzeGeneralBtn.addEventListener('click', () => handleAnalysisClick(analyzeGeneralBtn, generalResultDiv, '/analyze/general', youtubeData));
    analyzeThumbnailsBtn.addEventListener('click', () => handleAnalysisClick(analyzeThumbnailsBtn, thumbnailResultDiv, '/analyze/thumbnails', { videos: youtubeData.videos }));
    analyzeCommentsBtn.addEventListener('click', () => handleAnalysisClick(analyzeCommentsBtn, commentResultDiv, '/analyze/comments', { comments: youtubeData.comments }));
    analyzeTitlesBtn.addEventListener('click', () => handleAnalysisClick(analyzeTitlesBtn, titleSuggestionResultDiv, '/analyze/title-suggestions', youtubeData));

    // Event Listener untuk collapsible (tidak berubah)
    resultsPanel.addEventListener('click', (event) => {
        const trigger = event.target.closest('.collapse-trigger');
        if (!trigger) return;
        const content = trigger.nextElementSibling;
        const arrow = trigger.querySelector('.arrow-icon');
        content.classList.toggle('hidden');
        if (content.classList.contains('hidden')) {
            arrow.textContent = '▼';
        } else {
            arrow.textContent = '▲';
        }
    });
});