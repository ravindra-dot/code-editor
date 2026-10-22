let editor;
const initialEditor = window.initialEditor;
const draftKey = "codesphere-editor-draft";
let draft = null;
try { draft = JSON.parse(sessionStorage.getItem(draftKey)); } catch (_) { /* Ignore a damaged draft. */ }
if (!initialEditor && draft && ["python", "c", "cpp"].includes(draft.language)) {
    document.getElementById("language-select").value = draft.language;
}
const themeButton = document.getElementById("theme-toggle");
const editorStatus = document.getElementById("editor-status");
let editorTheme = "dark";
try {
    if (localStorage.getItem("codesphere-editor-theme") === "light") editorTheme = "light";
} catch (_) { /* Storage can be disabled by the browser. */ }
function applyEditorTheme() {
    if (editor) monaco.editor.setTheme(editorTheme === "light" ? "vs" : "vs-dark");
    document.getElementById("code").style.background = editorTheme === "light" ? "#ffffff" : "#020617";
    if (typeof terminal !== "undefined") {
        terminal.options.theme = editorTheme === "light"
            ? { background: "#f8fafc", foreground: "#0f172a" }
            : { background: "#020617", foreground: "#e2e8f0" };
        document.getElementById("terminal").style.background = editorTheme === "light" ? "#f8fafc" : "#020617";
    }
    themeButton.textContent = editorTheme === "light" ? "Dark editor" : "Light editor";
    themeButton.setAttribute("aria-pressed", String(editorTheme === "light"));
}
themeButton.addEventListener("click", () => {
    editorTheme = editorTheme === "light" ? "dark" : "light";
    try { localStorage.setItem("codesphere-editor-theme", editorTheme); } catch (_) { /* Keep the current theme. */ }
    applyEditorTheme();
});
if (initialEditor && ["python", "c", "cpp"].includes(initialEditor.language)) {
    document.getElementById("language-select").value = initialEditor.language;
}

require.config({
    paths: {
        'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs'
    }
});

require(['vs/editor/editor.main'], function () {
    registerCompletions();
    editor = monaco.editor.create(document.getElementById('code'), {
        value: initialEditor ? initialEditor.code : (typeof draft?.code === "string" ? draft.code : `print("Hello World")`),
        language: document.getElementById("language-select").value === "python" ? "python" : "cpp",
        theme: editorTheme === "light" ? "vs" : "vs-dark",
        automaticLayout: true,
        fontSize: 14,
        quickSuggestions: true,
        suggestOnTriggerCharacters: true,
        wordBasedSuggestions: "currentDocument",
        autoClosingBrackets: "always",
        autoClosingQuotes: "always",
        formatOnType: true,
        minimap: {
            enabled: true
        }
    });
    editor.onDidChangeModelContent(rememberDraft);
    applyEditorTheme();
});

function rememberDraft() {
    if (!editor) return;
    try {
        sessionStorage.setItem(draftKey, JSON.stringify({
            language: document.getElementById("language-select").value,
            code: editor.getValue()
        }));
    } catch (_) { /* Storage can be disabled by the browser. */ }
}

const completions = {
    python: [
        ["print", "print(${1:value})"], ["input", "input(${1:prompt})"],
        ["def", "def ${1:name}(${2:args}):\n    ${0:pass}"],
        ["for", "for ${1:item} in ${2:items}:\n    ${0:pass}"],
        ["if", "if ${1:condition}:\n    ${0:pass}"],
        ["class", "class ${1:Name}:\n    def __init__(self):\n        ${0:pass}"],
        ["try", "try:\n    ${1:pass}\nexcept ${2:Exception} as error:\n    ${0:pass}"],
        ["import", "import ${1:module}"]
    ],
    cpp: [
        ["include", "#include <${1:iostream}>"],
        ["main", "int main() {\n    ${0:return 0;}\n}"],
        ["for", "for (int ${1:i} = 0; ${1:i} < ${2:n}; ++${1:i}) {\n    ${0}\n}"],
        ["if", "if (${1:condition}) {\n    ${0}\n}"],
        ["cout", "std::cout << ${1:value} << std::endl;"],
        ["cin", "std::cin >> ${1:value};"],
        ["printf", "printf(\"${1:format}\\n\"${2});"],
        ["scanf", "scanf(\"${1:format}\", ${2:&value});"]
    ]
};
function registerCompletions() {
    for (const language of ["python", "cpp"]) {
        monaco.languages.registerCompletionItemProvider(language, {
            provideCompletionItems(model, position) {
                const word = model.getWordUntilPosition(position);
                const range = {
                    startLineNumber: position.lineNumber, endLineNumber: position.lineNumber,
                    startColumn: word.startColumn, endColumn: word.endColumn
                };
                return { suggestions: completions[language].map(([label, insertText]) => ({
                    label, insertText, range,
                    kind: monaco.languages.CompletionItemKind.Snippet,
                    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                })) };
            }
        });
    }
}

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
    rememberDraft();
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
applyEditorTheme();
terminal.writeln("Press Run Code to start a program.");
document.getElementById("save-button").addEventListener("click", async () => {
    if (!editor) return;
    const button = document.getElementById("save-button");
    button.disabled = true;
    try {
        const response = await fetch("/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ language: document.getElementById("language-select").value, code: editor.getValue() })
        });
        const result = await response.json();
        editorStatus.textContent = response.status === 401 ? "Log in to save code. Your editor content stays here." : result.message;
        if (response.status === 401) {
            const link = document.createElement("a");
            link.href = "/login";
            link.textContent = " Log in";
            link.className = "text-blue-400 underline";
            editorStatus.append(link);
        }
    } catch (error) {
        editorStatus.textContent = `Save failed: ${error.message}`;
    } finally {
        button.disabled = false;
    }
});
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
