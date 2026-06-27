/**
* PHP Email Form Validation - v3.10
* URL: https://bootstrapmade.com/php-email-form/
* Author: BootstrapMade.com
*/
(function () {
  "use strict";

  let forms = document.querySelectorAll('.php-email-form');

  forms.forEach(function (e) {
    e.addEventListener('submit', function (event) {
      event.preventDefault();
      let thisForm = this;

      let action = thisForm.getAttribute('action');
      let recaptcha = thisForm.getAttribute('data-recaptcha-site-key');

      if (!action) {
        displayError(thisForm, 'The form action property is not set!');
        return;
      }

      let loading = thisForm.querySelector('.loading');
      let errorMessage = thisForm.querySelector('.error-message');
      let successMessage = thisForm.querySelector('.sent-message');

      if (loading) loading.style.display = "block";
      if (errorMessage) errorMessage.style.display = "none";
      if (successMessage) successMessage.style.display = "none";

      let formData = new FormData(thisForm);

      if (recaptcha) {
        if (typeof grecaptcha !== "undefined") {
          grecaptcha.ready(function () {
            try {
              grecaptcha.execute(recaptcha, { action: 'php_email_form_submit' })
                .then(token => {
                  formData.set('recaptcha-response', token);
                  php_email_form_submit(thisForm, action, formData);
                })
            } catch (error) {
              displayError(thisForm, error);
            }
          });
        } else {
          displayError(thisForm, 'The reCaptcha JavaScript API is not loaded!');
        }
      } else {
        php_email_form_submit(thisForm, action, formData);
      }
    });
  });

  function php_email_form_submit(thisForm, action, formData) {
    fetch(action, {
      method: 'POST',
      body: formData,
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(response => response.text())
      .then(data => {
        let loading = thisForm.querySelector('.loading');
        let errorMessage = thisForm.querySelector('.error-message');
        let successMessage = thisForm.querySelector('.sent-message');

        if (loading) loading.style.display = "none";

        if (data.trim() === 'OK') {
          if (successMessage) {
            successMessage.style.display = "block";
          }
          thisForm.reset();
        } else {
          displayError(thisForm, data);
        }
      })
      .catch((error) => {
        displayError(thisForm, error);
      });
  }

  function displayError(thisForm, error) {
    let loading = thisForm.querySelector('.loading');
    let errorMessage = thisForm.querySelector('.error-message');

    if (loading) loading.style.display = "none";
    if (errorMessage) {
      errorMessage.innerHTML = error;
      errorMessage.style.display = "block";
    }
  }
})();
