(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", () => {
    const textarea = document.querySelector("#id_branding_css");
    const previewStyle = document.querySelector("#branding-preview-css");
    if (!textarea || !previewStyle) {
      return;
    }

    const updatePreview = () => {
      previewStyle.textContent = textarea.value;
    };

    textarea.addEventListener("input", updatePreview);
    updatePreview();
  });
})();
