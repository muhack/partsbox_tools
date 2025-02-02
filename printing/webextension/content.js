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
	const href_regex_parts = new RegExp(/.*?\/parts(?:\/|)$/);
	const href_regex_location = new RegExp(/.*?\/location\/\w{26}$/);
	const href_regex_storage = new RegExp(/.*?\/storage(?:\/|)$/);
	let link_regex;
	if (window.location.href.match(href_regex_parts) || window.location.href.match(href_regex_location)) {
		// Locations contain parts, so we need to check for both
		link_regex = new RegExp(/.*?\/parts\/\w{26}$/);
	} else if (window.location.href.match(href_regex_storage)) {
		link_regex = new RegExp(/.*?\/location\/\w{26}$/);
	} else {
		console.log("Unknown page type when trying to print selected parts");
		return;
	}
	let urls = [];
	selected.forEach((item) => {
		let partLinks = Array.from(item.querySelectorAll('a'));
		let url = partLinks.filter(part => link_regex.test(part.href)).map(part => part.href)
		urls = urls.concat(url);
	});
	sendURLs(urls);
}

// Taken from https://stackoverflow.com/a/61511955
function waitForElm(selector) {
	return new Promise(resolve => {
		if (document.querySelector(selector)) {
			return resolve(document.querySelector(selector));
		}

		const observer = new MutationObserver(mutations => {
			if (document.querySelector(selector)) {
				observer.disconnect();
				resolve(document.querySelector(selector));
			}
		});
		observer.observe(document.body, {
			childList: true,
			subtree: true
		});
	});
}

function onSelectedClick() {
	waitForElm("div.ui.secondary.small.vertical.menu>a.item").then((firstVertMenuButton) => {
		if (document.querySelector("#print-selected"))
			return;

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
}

// Add "Print" button to the vertical menu under the "Selected" button
function addPrintSelectedButton() {
	waitForElm("div.right.menu:has(div.button)>div:has(div.button)").then((selectedButton) => {
		selectedButton.addEventListener("click", onSelectedClick);
	});
}
function addPrintSelectedFromStorageButton() {
	waitForElm('div.ui.segment div.flexheader div.ui.tiny.button').then((selectedButton) => {
		selectedButton.addEventListener("click", onSelectedClick);
	});
}

// Add "Print" button to the part page
function addPrintEntityButton() {
	waitForElm("div.id-anything").then((idAnythingButton) => {
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

		idAnythingButton.parentNode.appendChild(printButton); // Print to the right of the ID-Anything button
	});
}

// Register an observer to add buttons whenever the page changes
const observer = new MutationObserver(() => {
	addPrintEntityButton();
	addPrintSelectedButton();
	addPrintSelectedFromStorageButton();
});
observer.observe(document.body, {
	childList: true,
	subtree: true
});
