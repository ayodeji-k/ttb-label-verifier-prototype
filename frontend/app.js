document.addEventListener('DOMContentLoaded', function () {
  const fileInput = document.getElementById('fileInput');
  const uploadBtn = document.getElementById('uploadBtn');
  const imgPreview = document.getElementById('imgPreview');
  const previewSection = document.getElementById('preview');
  const resultsDiv = document.getElementById('results');

  let currentFile = null;

  fileInput.addEventListener('change', (e) => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    currentFile = f;
    const url = URL.createObjectURL(f);
    imgPreview.src = url;
    previewSection.hidden = false;
  });

  uploadBtn.addEventListener('click', async () => {
    if (!currentFile) {
      alert('Choose an image first');
      return;
    }
    const form = new FormData();
    form.append('file', currentFile);
    // no application_brand for now
    resultsDiv.innerHTML = 'Processing...';
    const resp = await fetch('/api/extract', { method: 'POST', body: form});
    if (!resp.ok) {
      resultsDiv.innerHTML = 'Error: ' + resp.statusText;
      return;
    }
    const data = await resp.json();
    renderResults(data);
  });

  function renderResults(data) {
    const f = data.fields || {};
    resultsDiv.innerHTML = `
      <h3>Extracted Fields</h3>
      <ul>
        <li><strong>Brand candidate:</strong> ${f.brand_candidate || '-'} (${f.brand_score || '-'})</li>
        <li><strong>ABV:</strong> ${f.abv || '-'}</li>
        <li><strong>Net contents:</strong> ${f.net_contents || '-'}</li>
        <li><strong>Government warning OK:</strong> ${f.government_warning?.ok ? 'Yes' : 'No'}</li>
      </ul>
      <h4>OCR text (snippet)</h4>
      <pre style="max-height:200px; overflow:auto;">${(data.ocr_text || '').slice(0,2000)}</pre>
      <p><em>Latency: ${Math.round(data.latency_ms)} ms</em></p>
    `;
  }
});
