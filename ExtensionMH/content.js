// Inject content into the email message field and TinyMCE editor
function setEmailContent(content, retries = 10) {
  // Direct iframe injection
  const iframe = document.getElementById('email_msg_ifr');
  if (iframe && iframe.contentDocument && iframe.contentDocument.body) {
    iframe.contentDocument.body.innerHTML = content;
    return;
  }
  // Retry if not ready
  if (retries > 0) {
    setTimeout(() => setEmailContent(content, retries - 1), 300);
  } else {
    // Warning
    console.warn('TinyMCE editor not ready after multiple attempts.');
  }
}

function waitForFormAndInitialize() {
  const form = document.querySelector('#payment_form');
  if (!form) {
    console.log('Waiting for #payment_form...');
    setTimeout(waitForFormAndInitialize, 500);
    return;
  }

  console.log('Form found. Listening for CSV data...');

  window.addEventListener('csvDataReady', (event) => {
    // Enable the "Different prices per member" checkbox
    const indvPriceCheckbox = document.getElementById('indv_price');
    if (indvPriceCheckbox && !indvPriceCheckbox.checked) {
      indvPriceCheckbox.checked = true;
      indvPriceCheckbox.dispatchEvent(new Event('click', { bubbles: true }));
    }
    // Example usage: set your desired email content here
    setEmailContent('Hi,<br>Thank you for your recent interaction with the club. Please make this payment as soon as possible- Thanks :)<br>Full details including the payment deadline and a cost breakdown (if appropriate) will be sent seperately.<br>If you have any questions, please contact the club at <a href="mailto:sucp@soton.ac.uk?subject=Query%20MH%20Payment%20Request&body=Dear SUCP Treasurer,">sucp@soton.ac.uk</a>.<br>Best wishes,<br>SUCP Committee<br><br>---<br>This is an automated message created by the SUCP-MH Autofill System.');
    
    // Enable the "No deadline" checkbox and disable the deadline input
    const noDeadlineCheckbox = document.getElementById('no_deadline');
    const deadlineInput = document.getElementById('deadline');
    if (noDeadlineCheckbox && !noDeadlineCheckbox.checked) {
      noDeadlineCheckbox.checked = true;
      noDeadlineCheckbox.dispatchEvent(new Event('click', { bubbles: true }));
    }
    // Select "Match/Competition fees" in the reason dropdown
    const reasonSelect = document.getElementById('reason');
    if (reasonSelect) {
      reasonSelect.value = "21";
      reasonSelect.dispatchEvent(new Event('change', { bubbles: true }));
    }
    const csvText = event.detail;
    const rows = csvText.split('\n').slice(1); // Skip header

    rows.forEach(line => {
      const [firstName, lastName, cost] = line.split(',').map(s => s?.trim());
      if (!firstName || !lastName || !cost) return;

      const tableRows = document.querySelectorAll('#payment_form tbody tr');
      tableRows.forEach(row => {
        const lastNameCell = row.querySelector('td:nth-child(2) label');
        const firstNameCell = row.querySelector('td:nth-child(3) label');
        const checkbox = row.querySelector('input[type="checkbox"]');
        const costInput = row.querySelector('input[type="number"]');

        if (
          lastNameCell?.innerText.trim() === lastName &&
          firstNameCell?.innerText.trim() === firstName
        ) {
          console.log(`Filling ${firstName} ${lastName} with £${cost}`);
          checkbox.checked = true;
          costInput.disabled = false;
          costInput.value = cost;
        }
      });
    });
  });
}

waitForFormAndInitialize();

console.log('TinyMCE:', window.tinymce);
if (window.tinymce) {
  console.log('TinyMCE editors:', window.tinymce.editors.map(e => e.id));
}