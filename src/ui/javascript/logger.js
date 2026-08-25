class Logger {
	
	constructor() {
		this.#logViewer = document.getElementById('logViewer');
		this.#levelFilter = document.getElementById('levelFilter');
	}

	/**
	 * Appends a new structured log entry to the UI component.
	 * @param {string} message - The main log message string.
	 * @param {string} level - severity tier: 'info', 'warn', 'error', 'debug'
	 */
	appendLog(message, level = 'info') {
		const timestamp = new Date().toISOString().split('T')[1].slice(0, -1); // Formats as HH:MM:SS.sss
		
		// Create elements safely to prevent XSS issues
		const row = document.createElement('div');
		row.className = `log-row log-${level}`;
		row.setAttribute('data-level', level);

		const timeSpan = document.createElement('span');
		timeSpan.className = 'timestamp';
		timeSpan.textContent = timestamp;

		const levelSpan = document.createElement('span');
		levelSpan.className = 'level';
		levelSpan.textContent = level;

		const msgSpan = document.createElement('span');
		msgSpan.className = 'message';
		msgSpan.textContent = message;

		// Assemble row
		row.appendChild(timeSpan);
		row.appendChild(levelSpan);
		row.appendChild(msgSpan);

		// Hide entry immediately if it doesn't match active filter
		const activeFilter = this.#levelFilter.value;
		if (activeFilter !== 'all' && activeFilter !== level) {
			row.classList.add('hidden');
		}

		// Append container and snap visibility downward
		this.#logViewer.appendChild(row);
		this.#logViewer.scrollTop = this.#logViewer.scrollHeight;
	}

	// Dropdown interactive filter function
	filterLogs() {
		const selectedLevel = this.#levelFilter.value;
		const rows = this.#logViewer.querySelectorAll('.log-row');

		rows.forEach(row => {
			const rowLevel = row.getAttribute('data-level');
			if (selectedLevel === 'all' || rowLevel === selectedLevel) {
				row.classList.remove('hidden');
			} else {
				row.classList.add('hidden');
			}
		});
	}

	// Clear target DOM container completely
	clearLogs() {
		this.#logViewer.innerHTML = '';
	}

	// Dummy pipeline for simulation button
	#mockMessages = [
		{ text: "Database connection initialized cleanly.", level: "info" },
		{ text: "API endpoint query response duration clocked high: 1420ms.", level: "warn" },
		{ text: "Failed to resolve handshake with microservice authentication agent.", level: "error" },
		{ text: "Executing garbage collection sweep on heap pool memory allocation.", level: "debug" },
		{ text: "User session cache synchronized successfully across regional clusters.", level: "info" }
	];

	generateMockLog() {
		const randomLog = this.#mockMessages[Math.floor(Math.random() * this.#mockMessages.length)];
		appendLog(randomLog.text, randomLog.level);
	}
}

// Seed initial display entries
appendLog("System initializing execution tree...", "info");
appendLog("Debug flags verified actively listening.", "debug");
appendLog("Cron worker pool reporting standard operational thresholds.", "info");
	