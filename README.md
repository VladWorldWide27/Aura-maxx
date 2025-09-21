BetterPath: Accessible, community informed navigation

Built for SteelHacks XII

Contributors: Simon Goldin (Simongoldin06@gmail.com), Vladimir Deianov (Deyanovva@gmail.com), Diana Lysova (dianaelysova@gmail.com), Evgenii Venediktov (e.i.venediktov@gmail.com)

Languages, frameworks, and libraries: MapBox API, Gemini API, Python, TypeScript, Node.js, MongoDB

BetterPath is a navigation app that allows users to upload photos of hazards to further inform navigation and ETA. The project was designed with accessibility in mind, as it navigates users to the nearest accessible entrance.

The backend includes coords.py, database.py, graph_edge.py, graph_node.py, and obstacle.py, all of which serve as a comprehensive navigation framework that maps building and hazard coordinates.
The frontend includes script.js and index.html, which create a visually appealing map interface for the user using MapBox API.
The navigation components, build_graph.py, coordinate_calc.py, google_tts.py, graph_points.txt, navigator.py, requirements.txt, result_graph.txt, and streets_list.txt all fit into the backend and store the respective information needed.
The eponymous fastAPI.py creates the API for our program.
Photo validation comes from gemini_obstacle_detector.py, which takes a user uploaded photo, verifies the obstacle shown, and changes the navigation as a result of the photo's hazard.
Optional vertical navigation comes from insideEstimate.ts, which estimates time to a specific floor and further focuses the ETA.
Requirements.txt include our libraries.

How to set up and install the project:
cd into the folder
figure it our from there
