// Add options for each year from 1985 to 2020
for (var year = 1985; year <= 2020; year++) {
    var selected = year == 1985 ? "selected" : "";
    document.getElementById('startYear').innerHTML += '<option value="' + year + '" ' + selected + '>' + year + '</option>';
}

// Add options for each year from 1985 to 2020
for (var year = 1985; year <= 2020; year++) {
    var selected = year == 2020 ? "selected" : "";
    document.getElementById('endYear').innerHTML += '<option value="' + year + '" ' + selected + '>' + year + '</option>';
}

// Get the startYear and endYear elements
var startYear = document.getElementById("startYear");
var endYear = document.getElementById("endYear");

// Add an event listener to the startYear dropdown
startYear.addEventListener("change", function() {
    // Get the selected start year
    var selectedYear = this.value;

    // Store the currently selected end year
    var currentEndYear = endYear.value;

    // Clear the endYear dropdown
    endYear.innerHTML = "";

    // Add options to the endYear dropdown that are greater than or equal to the selected start year
    for (var year = selectedYear; year <= 2020; year++) {
        var option = document.createElement("option");
        option.value = year;
        option.text = year;
        endYear.add(option);

        // If the current end year is greater than or equal to the selected start year, keep it selected
        if (year == currentEndYear) {
            option.selected = true;
        }
    }
});

// Add an event listener to the endYear dropdown
endYear.addEventListener("change", function() {
    // Get the selected end year
    var selectedYear = this.value;

    // Store the currently selected start year
    var currentStartYear = startYear.value;

    // Clear the startYear dropdown
    startYear.innerHTML = "";

    // Add options to the startYear dropdown that are less than or equal to the selected end year
    for (var year = 1985; year <= selectedYear; year++) {
        var option = document.createElement("option");
        option.value = year;
        option.text = year;
        startYear.add(option);

        // If the current start year is less than or equal to the selected end year, keep it selected
        if (year == currentStartYear) {
            option.selected = true;
        }
    }
});
