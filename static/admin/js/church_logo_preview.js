(function () {
  "use strict";

  function setPreviewSrc(src) {
    document.querySelectorAll("[data-logo-preview]").forEach((img) => {
      img.src = src;
    });
    document.querySelectorAll("[data-logo-preview-sidebar]").forEach((img) => {
      img.src = src;
    });
    document.querySelectorAll("[data-logo-preview-mobile]").forEach((img) => {
      img.src = src;
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.querySelector("#id_logo");
    if (!fileInput) {
      return;
    }

    fileInput.addEventListener("change", () => {
      const file = fileInput.files && fileInput.files[0];
      if (!file) {
        return;
      }
      const reader = new FileReader();
      reader.addEventListener("load", () => setPreviewSrc(reader.result));
      reader.readAsDataURL(file);
    });
  });
})();
