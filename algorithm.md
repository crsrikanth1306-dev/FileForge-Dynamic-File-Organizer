# FileForge Algorithm

## Input
A user-selected directory containing files.

## Output
Files grouped into category folders and a `fileforge_report.json` summary.

## Steps
1. Validate that the selected path exists and is a directory.
2. Scan files in the selected directory.
3. For each file, convert its extension to lowercase.
4. Search the extension rules to determine a category; use `Others` if no rule matches.
5. Create a destination path for the file.
6. In preview mode, show the proposed destination without moving files.
7. In execution mode, create the category directory if it does not exist.
8. If a filename already exists at the destination, append a number to create a unique name.
9. Move the file using `shutil.move`.
10. Catch file-system errors and add them to the report.
11. Save the report as JSON.

## Complexity
Let `n` be the number of files and `k` the number of category rules. The simple classification loop is O(n × k). Since the rule set is small and fixed, it behaves approximately linearly with the number of files. Space complexity is O(n) for the plan and report.

## Important design choices
- Preview mode reduces accidental changes.
- Duplicate protection prevents overwriting existing files.
- Unknown extensions are placed in `Others`.
- Error handling lets the application report failures rather than crash on the first issue.
