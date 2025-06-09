document.getElementById('fillForm').addEventListener('click', () => {
  const fileInput = document.getElementById('csvFile');
  const file = fileInput.files[0];

  if (!file) {
    alert('Please upload a CSV file.');
    return;
  }

  const reader = new FileReader();
  reader.onload = function (e) {
    const csvData = e.target.result;

    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
      chrome.scripting.executeScript({
        target: { tabId: tabs[0].id },
        func: (csv) => {
          window.dispatchEvent(new CustomEvent('csvDataReady', { detail: csv }));
        },
        args: [csvData]
      });
    });
  };

  reader.readAsText(file);
});
