const printerSvg = `<?xml version="1.0" ?><svg viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg"><rect fill="none" height="256" width="256"/><polyline fill="none" points="64 80 64 40 192 40 192 80" stroke="#000" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><rect fill="none" height="68" stroke="#000" stroke-linecap="round" stroke-linejoin="round" stroke-width="16" width="128" x="64" y="152"/><path d="M64,176H28V96c0-8.8,7.8-16,17.3-16H210.7c9.5,0,17.3,7.2,17.3,16v80H192" fill="none" stroke="#000" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><circle cx="188" cy="116" r="12"/></svg>`;


function printSelected() {
	const selected = Array.from(document.querySelectorAll('tr:has(input:not([id="all"]):checked)'));
	selected.forEach((item) => {
		let partLinks = Array.from(item.querySelectorAll('a'));
		let url = partLinks.filter(part => part.href.includes("/parts/") && !part.href.includes("/parts/o/"))
			.map(part => part.href)
		console.log(url);
	});
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
		if (source === document) {
			observer.observe(document.body, {
				childList: true,
				subtree: true
			});
		} else {
			observer.observe(source, {
				childList: true,
				subtree: true
			});
		}
	});
}

// Add "Print" button to the vertical menu under the "Selected" button
function addPrintSelectedButton() {
	waitForElm("div.right.menu:has(input)").then((rightMenu) => {
		waitForElm("div:has(div.button)", rightMenu).then((selectedButton) => {
			selectedButton.addEventListener("click", (e) => {
				if (document.querySelector("#print-selected"))
					return;
				waitForElm("a.item", e.target.parentNode).then((firstVertMenuButton) => {
					// Add "print" element before the first vertical menu button
					const printHref = document.createElement("a");
					printHref.className = "item";
					printHref.addEventListener("click", () => {
						printSelected();
					});
					printHref.id = "print-selected";

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

					firstVertMenuButton.parentNode.insertBefore(printHref, firstVertMenuButton);
				});
			});
		});
	});
}
// Add onclick to top "Parts" tab button
waitForElm("div#top-menu a[href*='parts']").then((partsTab) => {
	partsTab.addEventListener("click", () => {
		addPrintSelectedButton();
	});
});
addPrintSelectedButton(); // Call once to add button on page load
