function cleanNameValue(value) {
    var cleaned = value.replace(/[^a-zA-Z0-9_ ]/g, '').replace(/\s+/g, '_');
    return cleaned;
}

document.getElementById('name').addEventListener('input', function (e) {
    var input = e.target;
    input.value = cleanNameValue(input.value);
});
