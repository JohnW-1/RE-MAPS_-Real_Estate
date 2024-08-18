from qgis.core import QgsProject, QgsVectorLayer, QgsGeometry, QgsPointXY, QgsWkbTypes
from qgis.utils import iface
from qgis.PyQt.QtWidgets import (
    QInputDialog, QFileDialog, QMessageBox, QDialog, QVBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton, QHBoxLayout
)
import shutil, random, os, csv
from urllib.parse import unquote, quote, urlparse
from pathlib import Path

# Function to get vector layers of specific types
def get_vector_layers(layer_types=None):
    # Return a list of vector layers that match the specified types
    return [
        layer for layer in QgsProject.instance().mapLayers().values()
        if isinstance(layer, QgsVectorLayer) and (not layer_types or layer.wkbType() in layer_types)
    ]

# Function to get the layer by prompt
def get_layer_by_prompt(prompt, layer_types=None):
    # Prompt the user to select a layer from the available layers of the specified types
    layers = get_vector_layers(layer_types)
    layer_names = [layer.name() for layer in layers]
    layer_name, ok = QInputDialog.getItem(iface.mainWindow(), "Select Layer", prompt, layer_names, 0, False)
    return layers[layer_names.index(layer_name)] if ok else None

# Function to copy feature layer source file with overwrite confirmation
def copy_feature_layer_source_file(layer, new_name, new_directory):
    # Get the file path from the layer's source URI
    source_path = unquote(urlparse(layer.source()).path)
    # Create a new file path in the specified directory with the new name
    new_path = os.path.join(new_directory, new_name + os.path.splitext(source_path)[1])

    # If the new file path exists, ask the user for confirmation to overwrite it
    if os.path.exists(new_path):
        reply = QMessageBox.question(iface.mainWindow(), "File Exists", f"The file {new_path} already exists. Overwrite?", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return None
        os.remove(new_path)

    # Copy the source file to the new file path
    shutil.copy(source_path, new_path)
    return new_path

# Function to generate a random point within a polygon
def generate_random_point_within_polygon(polygon):
    point = QgsGeometry.fromPointXY(QgsPointXY(0, 0))
    # Generate random points until one is within the polygon
    while not point.within(polygon):
        x_min, y_min, x_max, y_max = polygon.boundingBox().toRectF().getCoords()
        point = QgsGeometry.fromPointXY(QgsPointXY(random.uniform(x_min, x_max), random.uniform(y_min, y_max)))
    return point

# Function to replace specific WKT strings in the copied file
def replace_wkt_strings(file_path, polygon, wkt_column):
    with open(file_path, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        lines = list(reader)

    header = lines[0]
    wkt_idx = header.index(wkt_column)

    with open(file_path, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)

        for parts in lines[1:]:
            if len(parts) > wkt_idx:
                wkt = parts[wkt_idx]
                # Replace (EMPTY) and (0 0) in the WKT with random points within the polygon
                while "(EMPTY)" in wkt or "(0 0)" in wkt:
                    wkt = wkt.replace("(EMPTY)", generate_random_point_within_polygon(polygon).asWkt())
                    wkt = wkt.replace("(0 0)", generate_random_point_within_polygon(polygon).asWkt())
                parts[wkt_idx] = wkt
            writer.writerow(parts)

# Class for the feature layer selection dialog
class FeatureLayerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Feature Layer and Save Location")
        layout = QVBoxLayout()

        self.layer_combo = self.create_layer_combo(layout)
        self.name_input = self.create_name_input(layout)
        self.dir_input = self.create_dir_input(layout)
        self.create_buttons(layout)
        self.setLayout(layout)

    def create_layer_combo(self, layout):
        layout.addWidget(QLabel("Select Feature Layer (Delimited Text Layer):"))
        layer_combo = QComboBox()
        self.layers = get_vector_layers([QgsWkbTypes.MultiPoint])
        for layer in self.layers:
            layer_combo.addItem(layer.name())
        layout.addWidget(layer_combo)
        return layer_combo

    def create_name_input(self, layout):
        layout.addWidget(QLabel("Enter new layer name:"))
        name_input = QLineEdit(f"modified_{self.layer_combo.currentText()}")
        layout.addWidget(name_input)
        return name_input

    def create_dir_input(self, layout):
        layout.addWidget(QLabel("Select Directory to Save Modified Feature Layer:"))
        dir_input = QLineEdit(QgsProject.instance().homePath())
        dir_button = QPushButton("Browse")
        dir_button.clicked.connect(self.browse_directory)
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(dir_input)
        dir_layout.addWidget(dir_button)
        layout.addLayout(dir_layout)
        return dir_input

    def create_buttons(self, layout):
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_button)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", self.dir_input.text())
        if directory:
            self.dir_input.setText(directory)

    def get_selected_layer(self):
        return self.layers[self.layer_combo.currentIndex()]

    def get_new_layer_name(self):
        return self.name_input.text()

    def get_selected_directory(self):
        return self.dir_input.text()

# Step 1: Prompt user to select a "Boundary Layer"
boundary_layer = get_layer_by_prompt("Select a Boundary Layer (Polygon or MultiPolygon Layer)", [QgsWkbTypes.Polygon, QgsWkbTypes.MultiPolygon])
if not boundary_layer:
    raise ValueError("Boundary Layer not selected or invalid type")

boundary_polygon = next(boundary_layer.getFeatures()).geometry()

# Create the feature layer selection dialog
dialog = FeatureLayerDialog(iface.mainWindow())
if not dialog.exec_():
    raise ValueError("Dialog canceled")

feature_layer = dialog.get_selected_layer()
new_layer_name = dialog.get_new_layer_name()
new_directory = dialog.get_selected_directory()

# Copy "Feature Layer" source file to the new directory with the new name
new_file_path = copy_feature_layer_source_file(feature_layer, new_layer_name, new_directory)
if not new_file_path:
    raise ValueError("Failed to create modified feature layer source file")

# Read the header to prompt for WKT column
with open(new_file_path, 'r', encoding='utf-8') as file:
    header = file.readline().strip().split(',')

# Prompt for WKT column selection
wkt_column, ok = QInputDialog.getItem(iface.mainWindow(), "Select WKT Column", "Select the WKT geometry column:", header, 0, False)
if not ok or not wkt_column:
    raise ValueError("No WKT column selected")

# Replace WKT strings in the copied file
replace_wkt_strings(new_file_path, boundary_polygon, wkt_column)

# Construct URI for delimited text layer
file_path = Path(new_file_path).resolve()
uri = f"file://{quote(str(file_path))}?type=csv&delimiter=,&wktField={wkt_column}&spatialIndex=no&crs=epsg:4326"

# Create and load new delimited text layer with WKT MULTIPOINT geometry
new_layer = QgsVectorLayer(uri, new_layer_name, "delimitedtext")

if not new_layer.isValid():
    raise ValueError(f"Failed to load the new modified feature layer as a delimited text layer: {new_layer.error().message()}")

QgsProject.instance().addMapLayer(new_layer)
iface.layerTreeView().refreshLayerSymbology(new_layer.id())
QMessageBox.information(iface.mainWindow(), "Success", "Modified feature layer created and loaded successfully")
