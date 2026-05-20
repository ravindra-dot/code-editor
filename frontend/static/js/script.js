let editor;

require.config({
    paths: {
        'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs'
    }
});

require(['vs/editor/editor.main'], function () {
    editor = monaco.editor.create(document.getElementById('code'), {
        value: `print("Hello World")`,
        language: "python",
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

function runCode() {
    const language = document.getElementById("language-select").value;
    const code = editor.getValue();
    const userInput = document.getElementById("input-box").value;
    const outputBox = document.getElementById("output-box");

    outputBox.textContent = "Running...";

    const data = {
        language: language,
        code: code,
        input: userInput
    };

    fetch("/run", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(data => {
        outputBox.textContent = data.output;
    })
    .catch(err => {
        outputBox.textContent = "Error: " + err.message;
    });
}