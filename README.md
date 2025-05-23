# Quiz grading automation scripts
1. `scan.py` is a utility for quickly scanning and archiving paper-based student quizzes. Instead of relying on external scanning apps, this script captures the image, prompts for the student ID, and saves the file in a structured format.

2. `validate-names.py` is a utility for validating student name entries in a scanned quiz dataset by dispalying the student's submission on the side for comparison. This reduced the risk of grading the wrong student due to human errors.

3. `grade.py` is a utility for grading scanned student quizzes using structured text-based markschemes. It parses markschemes in the format section:marks for criterion, criterion name, displays them in a GUI, and allows efficient student marking. The script automatically saves feedback and criterion-wise marks for each student to a csv file whenever entries are modified, ensuring no work is lost during grading.

4. `upload.py` is a utility for tracking which students' grades have been uploaded to the central Excel sheet. It helps ensure that no student is missed by comparing recorded feedback with the entries in the spreadsheet, clearly identifying which grades are pending upload.
