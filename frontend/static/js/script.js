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
        theme: "vs",
        automaticLayout: true,
        fontSize: 14,
        minimap: {
            enabled: true
        }

    });

});


// language mapping
const languageMap = {

    python: "python",
    c: "cpp",
    cpp: "cpp"

};
const starterCode={

python:`print("Hello World")`,

c:`#include <stdio.h>

int main(){
printf("Hello World");
return 0;
}`,

cpp:`#include <iostream>
using namespace std;

int main(){
cout<<"Hello World";
return 0;
}`

};


// language dropdown change
document.getElementById("language-select").addEventListener("change", function(){

    if(!editor) return;

    const selected = this.value;

    const monacoLang = languageMap[selected];

    monaco.editor.setModelLanguage(editor.getModel(), monacoLang);

    editor.setValue(starterCode[selected]);

});


// file open logic
document.getElementById("fileInput").addEventListener("change", function (event) {

    const file = event.target.files[0];

    if (!file) return;

    const fileName = file.name;

    document.getElementById("fileName").innerText = fileName;

    const ext = fileName.split('.').pop().toLowerCase();

    const languageSelect = document.getElementById("language-select");



    if (ext === "py") {

        languageSelect.value = "python";
        monaco.editor.setModelLanguage(editor.getModel(), "python");

    }

    else if (ext === "c") {

        languageSelect.value = "c";
        monaco.editor.setModelLanguage(editor.getModel(), "cpp");

    }

    else if (ext === "cpp") {

        languageSelect.value = "cpp";
        monaco.editor.setModelLanguage(editor.getModel(), "cpp");

    }



    const reader = new FileReader();

    reader.onload = function (e) {

        editor.setValue(e.target.result);

    };

    reader.readAsText(file);

});


// sidebar toggle
document.addEventListener("DOMContentLoaded", function () {

    const toggleButton = document.getElementById("toggleFileSection");

    const fileSection = document.querySelector(".file-section");

    toggleButton.addEventListener("click", function () {

        fileSection.classList.toggle("show");

    });

});


// run code
function runCode() {

    const language = document.getElementById("language-select").value;

    const code = editor.getValue();

    const userInput = document.getElementById("input-box").value;

    const outputBox = document.getElementById("output-box");


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