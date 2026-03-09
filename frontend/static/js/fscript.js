let currentFolderHandle = null;
let currentFileHandle = null;

async function selectFolder() {
  try {
    const dirHandle = await window.showDirectoryPicker();
    currentFolderHandle = dirHandle;

    document.getElementById("folderTree").innerHTML = "";

    await loadFiles(dirHandle);

  } catch (error) {
    console.error("Folder selection canceled:", error);
  }
}

async function loadFiles(dirHandle, parentElement = null) {

  for await (const entry of dirHandle.values()) {

    const listItem = document.createElement("li");
    listItem.textContent = entry.name;
    listItem.style.cursor = "pointer";
    listItem.style.fontWeight = entry.kind === "directory" ? "bold" : "normal";

    if (entry.kind === "directory") {

      let isExpanded = false;
      let sublist = document.createElement("ul");
      sublist.style.display = "none";

      listItem.addEventListener("click", async (event) => {

        event.stopPropagation();

        if (isExpanded) {
          sublist.style.display = "none";
          sublist.innerHTML = "";
        } else {
          await loadFiles(entry, sublist);
          sublist.style.display = "block";
        }

        isExpanded = !isExpanded;

      });

      listItem.appendChild(sublist);

    } else {

      listItem.addEventListener("click", async () => {
        await openFile(entry);
      });

    }

    if (parentElement) {
      parentElement.appendChild(listItem);
    } else {
      document.getElementById("folderTree").appendChild(listItem);
    }

  }

}

async function openFile(fileHandle) {

  try {

    const file = await fileHandle.getFile();
    const content = await file.text();

    currentFileHandle = fileHandle;

    document.getElementById("fileName").textContent = file.name;

    editor.setValue(content);

    setEditorLanguage(file.name);

  } catch (error) {

    console.error("Error opening file:", error);

  }

}

function setEditorLanguage(fileName) {

  const ext = fileName.split(".").pop().toLowerCase();

  let language = "plaintext";

  if (ext === "py") language = "python";
  else if (ext === "c") language = "c";
  else if (ext === "cpp") language = "cpp";
  else if (ext === "js") language = "javascript";
  else if (ext === "html") language = "html";
  else if (ext === "css") language = "css";

  monaco.editor.setModelLanguage(editor.getModel(), language);

}

async function saveFile() {

  if (!currentFileHandle) {

    alert("No file selected!");
    return;

  }

  try {

    const writable = await currentFileHandle.createWritable();

    await writable.write(editor.getValue());

    await writable.close();

    alert("File saved successfully!");

  } catch (error) {

    console.error("Error saving file:", error);

  }

}

async function downloadFolder() {

  if (!currentFolderHandle) {

    alert("No folder selected!");
    return;

  }

  const zip = new JSZip();

  async function addFilesToZip(dirHandle, folder) {

    for await (const entry of dirHandle.values()) {

      if (entry.kind === "file") {

        const file = await entry.getFile();
        const content = await file.arrayBuffer();

        folder.file(entry.name, content);

      } else {

        const subFolder = folder.folder(entry.name);

        await addFilesToZip(entry, subFolder);

      }

    }

  }

  await addFilesToZip(currentFolderHandle, zip);

  const zipBlob = await zip.generateAsync({ type: "blob" });

  const link = document.createElement("a");

  link.href = URL.createObjectURL(zipBlob);
  link.download = "folder.zip";

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

}

function toggleExplorer(){

    const explorer = document.getElementById("explorer");

    explorer.classList.toggle("collapsed");

    setTimeout(()=>{
        if(editor){
            editor.layout();
        }
    },300);

}