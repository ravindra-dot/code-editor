let editor;
const initialEditor = window.initialEditor;
if (initialEditor && ["python", "c", "cpp"].includes(initialEditor.language)) {
    document.getElementById("language-select").value = initialEditor.language;
}

require.config({
    paths: {
        'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs'
    }
});

require(['vs/editor/editor.main'], function () {
    editor = monaco.editor.create(document.getElementById('code'), {
        value: initialEditor ? initialEditor.code : `print("Hello World")`,
        language: initialEditor ? (initialEditor.language === "python" ? "python" : "cpp") : "python",
        theme: "vs-dark",
        automaticLayout: true,
        fontSize: 14,
        minimap: {
            enabled: true
        }
    });
});

const languageMap = {
    python: "python",
    c: "cpp",
    cpp: "cpp"
};

const starterCode = {
    python: `print("Hello World")`,
    c: `#include <stdio.h>\n\nint main(){\n    printf("Hello World");\n    return 0;\n}`,
    cpp: `#include <iostream>\nusing namespace std;\n\nint main(){\n    cout << "Hello World";\n    return 0;\n}`
};

document.getElementById("language-select").addEventListener("change", function () {
    if (!editor) return;

    const selected = this.value;
    const monacoLang = languageMap[selected];

    monaco.editor.setModelLanguage(editor.getModel(), monacoLang);
    editor.setValue(starterCode[selected]);
});

const fileInputElement = document.getElementById("fileInput");
if (fileInputElement) {
    fileInputElement.addEventListener("change", function (event) {
        const file = event.target.files[0];
        if (!file) return;

        const fileName = file.name;
        const fileNameDisplay = document.getElementById("fileName");
        if (fileNameDisplay) {
            fileNameDisplay.innerText = fileName;
        }

        const ext = fileName.split('.').pop().toLowerCase();
        const languageSelect = document.getElementById("language-select");

        if (ext === "py") {
            languageSelect.value = "python";
            monaco.editor.setModelLanguage(editor.getModel(), "python");
        } else if (ext === "c") {
            languageSelect.value = "c";
            monaco.editor.setModelLanguage(editor.getModel(), "cpp");
        } else if (ext === "cpp") {
            languageSelect.value = "cpp";
            monaco.editor.setModelLanguage(editor.getModel(), "cpp");
        }

        const reader = new FileReader();
        reader.onload = function (e) {
            editor.setValue(e.target.result);
        };
        reader.readAsText(file);
    });
}

document.addEventListener("DOMContentLoaded", function () {
    const toggleButton = document.getElementById("toggleFileSection");
    const fileSection = document.querySelector(".file-section");

    if (toggleButton && fileSection) {
        toggleButton.addEventListener("click", function () {
            fileSection.classList.toggle("show");
        });
    }
});

const terminal = new Terminal({
    cursorBlink: true,
    convertEol: true,
    fontSize: 13,
    theme: { background: "#020617", foreground: "#e2e8f0" }
});
terminal.open(document.getElementById("terminal"));
terminal.writeln("Press Run Code to start a program.");
let activeSession = null;
let inputQueue = Promise.resolve();

terminal.onData(data => {
    if (!activeSession) return;
    const id = activeSession;
    inputQueue = inputQueue.then(() => fetch(`/terminal/${id}/input`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input: data })
    })).catch(() => {});
});

async function runCode() {
    if (!editor || activeSession) return;
    const runButton = document.getElementById("run-button");
    const stopButton = document.getElementById("stop-button");
    runButton.disabled = true;
    terminal.clear();
    terminal.writeln("Starting...");
    try {
        const response = await fetch("/terminal", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                language: document.getElementById("language-select").value,
                code: editor.getValue()
            })
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.message || "Could not start program");
        activeSession = result.id;
        stopButton.disabled = false;
        terminal.clear();
        terminal.focus();
        let offset = 0;
        while (activeSession === result.id) {
            const pollResponse = await fetch(`/terminal/${result.id}?offset=${offset}`);
            const poll = await pollResponse.json();
            if (!pollResponse.ok) throw new Error(poll.message || "Terminal disconnected");
            if (poll.output) terminal.write(poll.output);
            offset = poll.offset;
            if (poll.done) break;
            await new Promise(resolve => setTimeout(resolve, 180));
        }
    } catch (error) {
        terminal.writeln(`\r\n${error.message}`);
    } finally {
        activeSession = null;
        runButton.disabled = false;
        stopButton.disabled = true;
    }
}

async function stopCode() {
    if (!activeSession) return;
    const id = activeSession;
    document.getElementById("stop-button").disabled = true;
    try {
        await fetch(`/terminal/${id}/stop`, { method: "POST" });
    } catch (error) {
        terminal.writeln(`\r\n${error.message}`);
    }
}
