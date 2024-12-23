function printSelected() {
	const selected = Array.from(document.querySelectorAll('tr:has(input:not([id="all"]):checked)'));
	selected.forEach((item) => {
		let partLinks = Array.from(item.querySelectorAll('a'));
		let url = partLinks.filter(part => part.href.includes("/parts/") && !part.href.includes("/parts/o/"))
			.map(part => part.href)
		console.log(url);
	});
}

function addPrintButton(someDiv) {
	if (document.querySelector("#print-button"))
		return;

	const printItem = document.createElement("div");
	printItem.className = "item";
	printItem.id = "print-item";

	// Create sub elements
	const subDiv = document.createElement("div");
	const printButton = document.createElement("div");
	printButton.className = "ui tiny button";
	printButton.textContent = "Print selected";

	someDiv.parentNode.insertBefore(printItem, someDiv);
	printItem.appendChild(subDiv);
	subDiv.appendChild(printButton);

	printButton.addEventListener("click", () => {printSelected();});
}

const observer = new MutationObserver(function (mutations, mutationInstance) {
	const selectedDiv = Array.from(document.querySelectorAll("div.item"))
		.find(button => button.textContent.includes("Selected..."));
	if (selectedDiv === undefined || selectedDiv.length === 0) {
		return;
	} else if (selectedDiv.length > 0) {
		console.log("Too many 'Selected...' buttons found, aborting");
		return;
	}
	addPrintButton(selectedDiv);
	mutationInstance.disconnect();
});

observer.observe(document, {
    childList: true,
    subtree:   true
});
