document.getElementById('htmlCode').addEventListener('input', RunCode);
document.getElementById('cssCode').addEventListener('input', RunCode);
document.getElementById('jsCode').addEventListener('input', RunCode);

function RunCode() {
    const htmlCode = document.getElementById('htmlCode').value;
    const cssCode = '<style>' + document.getElementById('cssCode').value + '</style>';
    const jsCode = document.getElementById('jsCode').value;

    const previewFrame = document.getElementById('preview');
    const previewDoc = previewFrame.contentDocument || previewFrame.contentWindow.document;

    previewDoc.open();
    previewDoc.write(htmlCode + cssCode);
    previewDoc.close();

    const script = previewDoc.createElement("script");
    script.textContent = jsCode;
    previewDoc.body.appendChild(script);
}

function toggleHTML() {
    const panel = document.getElementById("panel-html");
    const dot = document.getElementById("dot-html");
    const btn = document.getElementById("btn-html");

    if (panel.classList.contains("hidden")) {
        panel.classList.remove("hidden");
        dot.classList.remove("bg-slate-600");
        dot.classList.add("bg-amber-400");
        btn.classList.remove("opacity-50");
    } else {
        panel.classList.add("hidden");
        dot.classList.remove("bg-amber-400");
        dot.classList.add("bg-slate-600");
        btn.classList.add("opacity-50");
    }
}

function toggleCSS() {
    const panel = document.getElementById("panel-css");
    const dot = document.getElementById("dot-css");
    const btn = document.getElementById("btn-css");

    if (panel.classList.contains("hidden")) {
        panel.classList.remove("hidden");
        dot.classList.remove("bg-slate-600");
        dot.classList.add("bg-blue-400");
        btn.classList.remove("opacity-50");
    } else {
        panel.classList.add("hidden");
        dot.classList.remove("bg-blue-400");
        dot.classList.add("bg-slate-600");
        btn.classList.add("opacity-50");
    }
}

function toggleJS() {
    const panel = document.getElementById("panel-js");
    const dot = document.getElementById("dot-js");
    const btn = document.getElementById("btn-js");

    if (panel.classList.contains("hidden")) {
        panel.classList.remove("hidden");
        dot.classList.remove("bg-slate-600");
        dot.classList.add("bg-yellow-400");
        btn.classList.remove("opacity-50");
    } else {
        panel.classList.add("hidden");
        dot.classList.remove("bg-yellow-400");
        dot.classList.add("bg-slate-600");
        btn.classList.add("opacity-50");
    }
}

function ShowOutput() {
    const container = document.getElementById('preview-container');
    const editors = document.getElementById('editors-container');

    if (container.classList.contains("hidden")) {
        container.classList.remove("hidden");
        editors.classList.remove("md:w-full");
        editors.classList.add("md:w-1/2");
    } else {
        container.classList.add("hidden");
        editors.classList.remove("md:w-1/2");
        editors.classList.add("md:w-full");
    }
}

function checkDisplaySize() {
    const alertBox = document.getElementById('alertMessage');
    if (window.innerWidth < 750) {
        alertBox.classList.remove('hidden');
    } else {
        alertBox.classList.add('hidden');
    }
}

function reloadPage() {
    location.reload();
}

window.addEventListener('DOMContentLoaded', function() {
    checkDisplaySize();
    window.addEventListener('resize', checkDisplaySize);
});