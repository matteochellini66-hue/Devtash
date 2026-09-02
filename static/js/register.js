document.addEventListener("DOMContentLoaded", function () {
    const checkbox = document.getElementById("checkbox");
    const submitButton = document.getElementById("submit-button");

    submitButton.disabled = !checkbox.checked;

    checkbox.addEventListener("change", function () {
        submitButton.disabled = !checkbox.checked;
    });
});
