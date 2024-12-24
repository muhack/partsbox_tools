const printerSvg = `<?xml version="1.0" ?><svg viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg"><rect fill="none" height="256" width="256"/><polyline fill="none" points="64 80 64 40 192 40 192 80" stroke="#000" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><rect fill="none" height="68" stroke="#000" stroke-linecap="round" stroke-linejoin="round" stroke-width="16" width="128" x="64" y="152"/><path d="M64,176H28V96c0-8.8,7.8-16,17.3-16H210.7c9.5,0,17.3,7.2,17.3,16v80H192" fill="none" stroke="#000" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><circle cx="188" cy="116" r="12"/></svg>`;

const PRINT_SERVER_PORT = 9581;

// Send URLs to the native messaging host
function sendURLs(urls) {
	const xhr = new XMLHttpRequest();
	xhr.open("POST", `http://localhost:${PRINT_SERVER_PORT}/print`, true);
	xhr.setRequestHeader("Content-Type", "application/json");
	xhr.onreadystatechange = function() {
		if (xhr.readyState === 4 && xhr.status != 200)
			console.log("ReadyState: ", xhr.readyState, "Status: ", xhr.status, "Response: ", xhr.responseText);
	};
	xhr.send(JSON.stringify(urls));
}

function printSelected() {
	const selected = Array.from(document.querySelectorAll('tr:has(input:not([id="all"]):checked)'));
	urls = [];
	selected.forEach((item) => {
		let partLinks = Array.from(item.querySelectorAll('a'));
		let url = partLinks.filter(part => part.href.includes("/parts/") && !part.href.includes("/parts/o/"))
			.map(part => part.href)
		urls = urls.concat(url);
	});
	sendURLs(urls);
}

// Taken from https://stackoverflow.com/a/61511955
function waitForElm(selector, source = document) {
	return new Promise(resolve => {
		if (source.querySelector(selector)) {
			return resolve(source.querySelector(selector));
		}

		const observer = new MutationObserver(mutations => {
			if (source.querySelector(selector)) {
				observer.disconnect();
				resolve(source.querySelector(selector));
			}
		});
		observe_src = source === document ? document.body : source;
		observer.observe(observe_src, {
			childList: true,
			subtree: true
		});
	});
}
// Wait for a specific element (not a selector) to disappear from the DOM
function waitForNotElm(element) {
	return new Promise(resolve => {
		if (!document.body.contains(element)) {
			return resolve();
		}

		const observer = new MutationObserver(mutations => {
			if (!document.body.contains(element)) {
				observer.disconnect();
				resolve();
			}
		});
		observer.observe(document.body, {
			childList: true,
			subtree: true
		});
	});
}

// Add "Print" button to the vertical menu under the "Selected" button
function addPrintSelectedButton() {
	waitForElm("div.right.menu:has(div.button)>div:has(div.button)").then((selectedButton) => {
		selectedButton.addEventListener("click", (e) => {
			waitForElm("a.item", e.target.parentNode).then((firstVertMenuButton) => {
				if (document.querySelector("#print-selected")) {
					console.log("Print button already exists");
					return;
				}

				// Add "print" element before the first vertical menu button
				const printHref = document.createElement("a");
				printHref.id = "print-selected";
				printHref.className = "item";
				printHref.addEventListener("click", () => {
					printSelected();
				});
				// Add straight away to avoid duplicate buttons
				firstVertMenuButton.parentNode.insertBefore(printHref, firstVertMenuButton);

				const printSpan = document.createElement("span");
				printHref.appendChild(printSpan);

				// Add icon to print entry
				const icon = document.createElement("i");
				icon.className = "icon";
				printSpan.appendChild(icon);

				const svg = document.createElement("svg");
				svg.innerHTML = printerSvg;
				icon.appendChild(svg);

				// Add text to print entry
				const text = document.createElement("span");
				text.textContent = "Print";
				printSpan.appendChild(text);
			});
		});
	});
}

let selectedButton
waitForElm("div.right.menu:has(div.button)").then((e) => {
	selectedButton = e;
});
addPrintSelectedButton(); // Call once to add button on page load
// Add onclick to top "Parts" and "Storage" tab buttons
waitForElm("div#top-menu>a[href*='parts']").then((partsTab) => {
	Array.from(document.querySelectorAll('div#top-menu>a[href*="parts"],a[href*="storage"]')).forEach((tab) => {
		tab.addEventListener("click", () => {
			waitForNotElm(selectedButton).then(() => { // Wait for element to disappear and reappear (on new tab)
				waitForElm('div.right.menu:has(div.button)').then((e) => {
					selectedButton = e;
					addPrintSelectedButton();
				});
			});
		});
	});
});

// Add "Print" button to the part page
function addPrintPartButton() {
	waitForElm("div.part-header>div.part-header-items").then((idAnythingButton) => {
		if (document.querySelector("#print-part"))
			return;
		const printButton = document.createElement("div");
		printButton.className = "right floated ui tiny icon button";
		printButton.id = "print-part";
		printButton.addEventListener("click", () => {
			sendURLs([window.location.href]);
		});

		// Add icon to print entry
		const icon = document.createElement("i");
		icon.className = "icon";
		printButton.appendChild(icon);

		const svg = document.createElement("svg");
		svg.innerHTML = printerSvg;
		icon.appendChild(svg);

		// Add text to print entry
		const text = document.createElement("span");
		text.textContent = "Print";
		printButton.appendChild(text);

		idAnythingButton.parentNode.insertBefore(printButton, idAnythingButton);
	});
}
addPrintPartButton();

