const fs = require("fs");
const PdfPrinter = require("pdfmake");

// Use built-in fonts
const fonts = {
  Helvetica: {
    normal: "Helvetica",
    bold: "Helvetica-Bold",
    italics: "Helvetica-Oblique",
    bolditalics: "Helvetica-BoldOblique",
  },
};
const printer = new PdfPrinter(fonts);

const timetable = JSON.parse(fs.readFileSync("src/output/timetable_resolved.json", "utf8"));
const timeSlots = ["9-10", "10-11", "11-12", "12-1", "2-3", "3-4", "4-5"];

/**
 * A helper function to check if two class entries are identical.
 * This is used to identify 2-hour labs.
 * @param {Array} entries1 - The class entries from the first time slot.
 * @param {Array} entries2 - The class entries from the second time slot.
 * @returns {boolean} - True if the entries are identical.
 */
function areEntriesEqual(entries1, entries2) {
    if (!entries1 || !entries2 || entries1.length !== entries2.length) {
        return false;
    }
    // A simple and reliable way to compare the objects
    return JSON.stringify(entries1) === JSON.stringify(entries2);
}


// Build table for one day
function buildDayTable(day, data) {
  const headerRow = [{ text: "Section", style: "tableHeader" }, ...timeSlots.map(s => ({ text: s, style: "tableHeader" }))];
  const body = [headerRow];

  data.forEach((section) => {
    const row = [{ text: section.section, style: "sectionCell" }];
    
    // Use a 'for' loop to allow skipping the next slot when a lab is merged
    for (let i = 0; i < timeSlots.length; i++) {
      const slot = timeSlots[i];
      const nextSlot = timeSlots[i + 1];
      
      const entries = section[slot] || [];
      const nextEntries = section[nextSlot] || [];

      // --- LOGIC FOR MERGING 2-HOUR LABS ---
      // Check if it's a lab that continues into the next slot
      if (entries.length > 0 && entries[0].isLab && areEntriesEqual(entries, nextEntries)) {
        // This is a 2-hour lab, so we create a merged cell
        const cellContent = createCellContent(entries);
        cellContent.colSpan = 2; // Merge this cell with the next one
        row.push(cellContent);
        row.push({}); // Add an empty placeholder for the spanned cell
        i++; // IMPORTANT: Skip the next time slot since it's now part of the merged cell
        continue; // Move to the next iteration
      }

      // If it's not a merged lab, process the cell normally
      row.push(createCellContent(entries));
    }
    body.push(row);
  });

  return {
    table: {
      headerRows: 1,
      widths: [70, ...timeSlots.map(() => "*")],
      body,
    },
    layout: {
      hLineWidth: () => 0.5,
      vLineWidth: () => 0.5,
      hLineColor: () => "#444",
      vLineColor: () => "#444",
      paddingTop: () => 6,
      paddingBottom: () => 6,
    },
  };
}

/**
 * Creates the content for a single cell in the timetable.
 * @param {Array} entries - The array of classes/labs in a time slot.
 * @returns {object|string} - The pdfmake cell object or an empty string.
 */
function createCellContent(entries) {
  if (entries.length === 0) {
    return ""; // Empty cell
  } 
  
  if (entries.length === 1) {
    // Cell with a single class or lab
    const e = entries[0];
    return {
      stack: [
        { text: `${e.subject} (${e.teacher})`, bold: true },
        { text: `Room: ${e.room}` },
        e.isLab ? { text: `Group: ${e.group}`, italics: true } : {}
      ],
      fillColor: e.isLab ? "#fff176" : null, // yellow for labs
      alignment: "center",
      margin: [2, 4, 2, 4],
    };
  } 
  
  // --- LOGIC FOR PARALLEL LABS WITH HORIZONTAL LINE ---
  // Cell with multiple parallel labs
  return {
    table: {
      widths: ["*"],
      body: entries.map((e) => [
        {
          stack: [
            { text: `${e.subject} (${e.teacher})`, bold: true },
            { text: `Room: ${e.room}` },
            e.isLab ? { text: `Group: ${e.group}`, italics: true } : {}
          ],
          fillColor: e.isLab ? "#fff176" : null,
          alignment: "center",
          margin: [2, 4, 2, 4],
          border: [false, false, false, false], // No borders inside the nested table cells
        }
      ]),
    },
    layout: {
      // Draw a line ONLY BETWEEN the labs, not on the top or bottom.
      hLineWidth: (i, node) => (i > 0 && i < node.table.body.length) ? 0.5 : 0,
      vLineWidth: () => 0,
      hLineColor: () => "#aaa",
      paddingTop: (i) => i === 0 ? 0 : 4,
      paddingBottom: (i, node) => i === node.table.body.length - 1 ? 0 : 4,
    },
  };
}


function makeDocument() {
  const content = [];
  Object.keys(timetable).forEach((day, idx) => {
    if (idx > 0) content.push({ text: "", pageBreak: "before" });

    content.push({ text: day, style: "dayHeader", margin: [0, 0, 0, 10] });
    content.push(buildDayTable(day, timetable[day]));
  });

  return {
    content,
    styles: {
      dayHeader: { fontSize: 18, bold: true, alignment: "center", margin: [0, 0, 0, 12] },
      tableHeader: { bold: true, fillColor: "#e0e0e0", alignment: "center" },
      sectionCell: { bold: true, alignment: "center" },
    },
    defaultStyle: {
      font: "Helvetica",
      fontSize: 9,
    },
    pageOrientation: "landscape",
  };
}

const pdfDoc = printer.createPdfKitDocument(makeDocument());
pdfDoc.pipe(fs.createWriteStream("src/output/Timetable.pdf"));
pdfDoc.end();

console.log("✅ Timetable PDF generated with merged labs and parallel dividers!");
