const fs = require('fs');

/**
 * A utility function to perform a deep comparison of two class objects.
 * @param {object} class1 - The first class object.
 * @param {object} class2 - The second class object.
 * @returns {boolean} - True if the classes are identical.
 */
function areClassesEqual(class1, class2) {
    if (!class1 || !class2) return false;
    // A simple and effective way to compare plain JSON objects
    return JSON.stringify(class1) === JSON.stringify(class2);
}

try {
    // --- 1. READ AND PREPARE DATA ---
    const inputFilename = 'src/output/University_Master_Timetable.json';
    const outputFilename = 'src/output/timetable.json';
    
    if (!fs.existsSync(inputFilename)) {
        console.error(`Error: The input file "${inputFilename}" was not found.`);
        process.exit(1);
    }
    
    const timetableData = fs.readFileSync(inputFilename, 'utf8');
    const timetable = JSON.parse(timetableData);

    // Create a deep copy to modify, preserving the original data structure
    const newTimetable = JSON.parse(JSON.stringify(timetable));

    const timeSlots = ["9-10", "10-11", "11-12", "12-1", "2-3", "3-4", "4-5"];

    // --- 2. PROCESS THE TIMETABLE ---

    // Iterate over each day in the timetable (e.g., "Monday", "Tuesday")
    for (const day in newTimetable) {
        // For each day, iterate over every section's schedule
        for (const sectionSchedule of newTimetable[day]) {
            const labsForSection = []; // Stores all identified 2-hour labs for the section on this day
            const labSlotsToClear = new Set(); // Stores the time slots of the original labs to be cleared

            // Find all 2-hour lab blocks for the current section
            for (let i = 0; i < timeSlots.length - 1; i++) {
                const slot1 = timeSlots[i];
                const slot2 = timeSlots[i + 1];

                const class1Array = sectionSchedule[slot1];
                const class2Array = sectionSchedule[slot2];

                // A valid 2-hour lab block consists of two consecutive, identical, single-lab slots
                if (
                    class1Array && class1Array.length === 1 && class1Array[0].isLab &&
                    class2Array && class2Array.length === 1 &&
                    areClassesEqual(class1Array[0], class2Array[0])
                ) {
                    labsForSection.push({
                        details: class1Array[0],
                        startTime: slot1
                    });
                    
                    labSlotsToClear.add(slot1);
                    labSlotsToClear.add(slot2);
                    
                    i++; // Skip the next time slot as it has been processed
                }
            }

            // If two or more distinct 2-hour labs are found for the same section, they need to be merged
            if (labsForSection.length > 1) {
                // a) Clear all the original lab slots
                for (const slot of labSlotsToClear) {
                    sectionSchedule[slot] = [];
                }

                // b) The labs are already sorted by time; the first one is the earliest.
                const earliestLab = labsForSection[0];
                const startTimeIndex = timeSlots.indexOf(earliestLab.startTime);
                
                const parallelSlot1 = timeSlots[startTimeIndex];
                const parallelSlot2 = timeSlots[startTimeIndex + 1];

                // c) Collect the details of all labs to be run in parallel
                const allLabDetails = labsForSection.map(lab => lab.details);
                
                // d) Assign the merged list of parallel labs to the new 2-hour time slot
                sectionSchedule[parallelSlot1] = allLabDetails;
                sectionSchedule[parallelSlot2] = allLabDetails;
            }
        }
    }

    // --- 3. WRITE THE OUTPUT FILE ---
    fs.writeFileSync(outputFilename, JSON.stringify(newTimetable, null, 2));
    console.log(`✅ Success! Modified timetable has been saved to "${outputFilename}".`);

} catch (error) {
    console.error("An error occurred during processing:", error);
}