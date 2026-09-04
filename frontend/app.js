document.addEventListener('DOMContentLoaded', function () {
  const fileInput = document.getElementById('fileInput');
  const uploadBtn = document.getElementById('uploadBtn');
  const thumbnails = document.getElementById('thumbnails');
  const previewSection = document.getElementById('preview');
  const resultsDiv = document.getElementById('results');

  let currentFiles = [];

  fileInput.addEventListener('change', (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    currentFiles = files;
    thumbnails.innerHTML = '';
    for (const f of files) {
      const url = URL.createObjectURL(f);
      const img = document.createElement('img');
      img.src = url;
      img.alt = f.name;
      img.style.maxWidth = '180px';
      img.style.margin = '8px';
      thumbnails.appendChild(img);
    }
    resultsDiv.innerHTML = '';
    previewSection.hidden = false;
  });

  uploadBtn.addEventListener('click', async () => {
    if (!currentFiles.length) {
      alert('Choose one or more images first');
      return;
    }
    const form = new FormData();
    for (const f of currentFiles) {
      form.append('files', f, f.name);
    }
    resultsDiv.innerHTML = '<p>Processing batch... <em>(this may take a few seconds)</em></p>';
    try {
      const resp = await fetch('/api/batch-extract', { method: 'POST', body: form});
      if (!resp.ok) {
        resultsDiv.innerHTML = 'Error: ' + resp.statusText;
        return;
      }
      const data = await resp.json();
      renderBatchResults(data);
    } catch (err) {
      resultsDiv.innerHTML = 'Error: ' + err.message;
    }
  });

  function renderBatchResults(data) {
    const res = data.results || [];
    resultsDiv.innerHTML = `<p>Processed ${res.length} items in ${Math.round(data.total_latency_ms)} ms</p>`;
    const list = document.createElement('div');
    list.style.display = 'grid';
    list.style.gridTemplateColumns = '1fr 2fr';
    list.style.gap = '12px';

    for (const item of res) {
      const left = document.createElement('div');
      left.innerHTML = `<strong>${item.filename}</strong><br/><em>Latency: ${Math.round(item.latency_ms || 0)} ms</em>`;
      const right = document.createElement('div');
      if (item.error) {
        right.textContent = 'Error: ' + item.error;
      } else {
        const f = item.fields || {};
        right.innerHTML = `
          <ul>
            <li><strong>Brand candidate:</strong> ${f.brand_candidate || '-'} (${f.brand_score || '-'})</li>
            <li><strong>ABV:</strong> ${f.abv || '-'}</li>
            <li><strong>Net contents:</strong> ${f.net_contents || '-'}</li>
            <li><strong>Government warning OK:</strong> ${f.government_warning?.ok ? 'Yes' : 'No'}</li>
          </ul>
          <details><summary>OCR text (snippet)</summary><pre style="max-height:150px; overflow:auto;">${(item.ocr_text || '').slice(0,1500)}</pre></details>
        `;
      }
      list.appendChild(left);
      list.appendChild(right);
    }
    resultsDiv.appendChild(list);
  }
});
