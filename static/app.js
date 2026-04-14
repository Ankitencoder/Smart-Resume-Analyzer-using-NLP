const form = document.getElementById('analyzeForm');
const results = document.getElementById('results');
const errorText = document.getElementById('error');

function populateList(id, items) {
  const ul = document.getElementById(id);
  ul.innerHTML = '';
  if (!items || items.length === 0) {
    const li = document.createElement('li');
    li.textContent = 'None';
    ul.appendChild(li);
    return;
  }
  items.forEach((item) => {
    const li = document.createElement('li');
    li.textContent = item;
    ul.appendChild(li);
  });
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  errorText.textContent = '';
  results.classList.add('hidden');

  const formData = new FormData(form);

  try {
    const response = await fetch('/analyze', {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Unable to analyze resume.');
    }

    document.getElementById('score').textContent = data.score;
    populateList('skills', data.skills);
    populateList('missing_keywords', data.missing_keywords);
    populateList('suggestions', data.suggestions);
    results.classList.remove('hidden');
  } catch (err) {
    errorText.textContent = err.message;
  }
});
