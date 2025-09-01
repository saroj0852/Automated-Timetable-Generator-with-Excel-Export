const fs = require('fs');

const TIME_SLOTS = ["9-10", "10-11", "11-12", "12-1", "2-3", "3-4", "4-5"];

// --- CHANGE START ---
// Define the only valid starting times for a 2-hour lab block.
const VALID_LAB_START_SLOTS = ["9-10", "11-12", "3-4"];
// --- CHANGE END ---


/**
 * Builds a comprehensive map of who/what is busy during each time slot of a given day.
 * @param {Array} dailyScheduleData - The array of section schedules for one day.
 * @returns {object} An object containing usage maps for teachers, rooms, and sections.
 */
function buildDailyUsage(dailyScheduleData) {
    const usage = { teachers: {}, rooms: {}, sections: {} };

    for (const section of dailyScheduleData) {
        usage.sections[section.section] = {};
        for (const slot of TIME_SLOTS) {
            if (section[slot] && section[slot].length > 0) {
                // Mark section as busy
                usage.sections[section.section][slot] = true;
                
                for (const classInfo of section[slot]) {
                    // Mark teacher as busy
                    if (!usage.teachers[classInfo.teacher]) usage.teachers[classInfo.teacher] = {};
                    usage.teachers[classInfo.teacher][slot] = true;
                    
                    // Mark room as busy and track who is using it
                    if (!usage.rooms[classInfo.room]) usage.rooms[classInfo.room] = {};
                    if (!usage.rooms[classInfo.room][slot]) usage.rooms[classInfo.room][slot] = [];
                    usage.rooms[classInfo.room][slot].push({ 
                        section: section.section,
                        details: classInfo 
                    });
                }
            }
        }
    }
    return usage;
}

/**
 * Finds the first available 2-hour slot for a lab from a list of valid slots.
 * @param {object} labToMove - The lab object needing a new slot.
 * @param {object} dailyUsage - The usage map for the day.
 * @returns {string|null} The starting time slot if found, otherwise null.
 */
function findNewSlot(labToMove, dailyUsage) {
    // --- CHANGE START ---
    // Iterate ONLY over the predefined valid lab start times.
    for (const slot1 of VALID_LAB_START_SLOTS) {
        const slot1Index = TIME_SLOTS.indexOf(slot1);
        const slot2 = TIME_SLOTS[slot1Index + 1]; // Get the next hour

        const isSectionFree = !dailyUsage.sections[labToMove.section]?.[slot1] && !dailyUsage.sections[labToMove.section]?.[slot2];
        const isTeacherFree = !dailyUsage.teachers[labToMove.details.teacher]?.[slot1] && !dailyUsage.teachers[labToMove.details.teacher]?.[slot2];
        const isRoomFree = !dailyUsage.rooms[labToMove.details.room]?.[slot1] && !dailyUsage.rooms[labToMove.details.room]?.[slot2];

        if (isSectionFree && isTeacherFree && isRoomFree) {
            return slot1; // Return the valid start time of the 2-hour slot
        }
    }
    // --- CHANGE END ---
    return null; // No valid and free slot found
}

/**
 * Moves a lab from its old slot to a new one within the timetable data structure.
 * @param {object} labToMove - The full lab object.
 * @param {string} oldSlotStart - The original conflicting start time.
 * @param {string} newSlotStart - The new, free start time.
 * @param {Array} dailySchedule - The array of section schedules for the day.
 */
function performMove(labToMove, oldSlotStart, newSlotStart, dailySchedule) {
    const oldSlotStartIndex = TIME_SLOTS.indexOf(oldSlotStart);
    const oldSlot2 = TIME_SLOTS[oldSlotStartIndex + 1];

    const newSlotStartIndex = TIME_SLOTS.indexOf(newSlotStart);
    const newSlot2 = TIME_SLOTS[newSlotStartIndex + 1];
    
    const sectionSchedule = dailySchedule.find(s => s.section === labToMove.section);
    if (!sectionSchedule) return;

    // 1. Remove from old slot
    sectionSchedule[oldSlotStart] = sectionSchedule[oldSlotStart].filter(c => c.subject !== labToMove.details.subject || c.group !== labToMove.details.group);
    sectionSchedule[oldSlot2] = sectionSchedule[oldSlot2].filter(c => c.subject !== labToMove.details.subject || c.group !== labToMove.details.group);

    // 2. Add to new slot
    if (!sectionSchedule[newSlotStart]) sectionSchedule[newSlotStart] = [];
    sectionSchedule[newSlotStart].push(labToMove.details);
    if (!sectionSchedule[newSlot2]) sectionSchedule[newSlot2] = [];
    sectionSchedule[newSlot2].push(labToMove.details);
}

// --- Main Execution ---
try {
    const inputFilename = 'src/output/timetable.json';
    const outputFilename = 'src/output/timetable_resolved.json';

    const timetableData = fs.readFileSync(inputFilename, 'utf8');
    const resolvedTimetable = JSON.parse(timetableData);

    console.log("🔍 Starting conflict resolution process...");

    for (const day in resolvedTimetable) {
        let conflictsResolvedInDay = 0;
        let hasUnresolvedConflicts = false;

        for (let i = 0; i < 10; i++) { 
            const usage = buildDailyUsage(resolvedTimetable[day]);
            let conflictFoundThisIteration = false;

            for (const room in usage.rooms) {
                for (const slot in usage.rooms[room]) {
                    const occupants = usage.rooms[room][slot];
                    if (occupants.length > 1) {
                        conflictFoundThisIteration = true;
                        
                        const labToMove = occupants[1]; 
                        console.log(`\n🚨 Conflict found on ${day} at ${slot} in room ${room}.`);
                        console.log(`   - Section "${occupants[0].section}" and "${labToMove.section}" are clashing.`);
                        console.log(`   - Attempting to move "${labToMove.details.subject}" for section "${labToMove.section}".`);

                        const newSlot = findNewSlot(labToMove, usage);

                        if (newSlot) {
                            performMove(labToMove, slot, newSlot, resolvedTimetable[day]);
                            console.log(`   - ✅ SUCCESS: Moved to new slot starting at ${newSlot}.`);
                            conflictsResolvedInDay++;
                        } else {
                            console.log(`   - ❌ FAILED: No available 2-hour slot found for this lab on ${day}.`);
                            hasUnresolvedConflicts = true;
                        }
                        break; 
                    }
                }
                if (conflictFoundThisIteration) break;
            }
            if (!conflictFoundThisIteration) break; 
        }
        if (hasUnresolvedConflicts) {
             console.warn(`\n⚠️ Please manually review ${day} for unresolved conflicts.`);
        }
    }

    fs.writeFileSync(outputFilename, JSON.stringify(resolvedTimetable, null, 2));
    console.log(`\n✨ Process complete! Resolved timetable saved to "${outputFilename}".`);

} catch (error) {
    console.error("An error occurred:", error);
}