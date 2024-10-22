import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QGraphicsView, QGraphicsScene, QTextEdit, QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsLineItem

from PyQt6.QtCore import Qt, QRectF, QPointF, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter
import math

class TaxonNode(QGraphicsEllipseItem):
    def __init__(self, name, x, y, parent=None):
        super().__init__(x - 5, y - 5, 10, 10, parent)
        self.name = name
        self.label = QGraphicsTextItem(name, self)
        self.label.setPos(x - self.label.boundingRect().width() / 2,
                         y - 25)
        self.setAcceptHoverEvents(True)
        self.setBrush(QBrush(QColor("#4299e1")))
        self.setPen(QPen(QColor("#2b6cb0")))
        
    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor("#63b3ed")))
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor("#4299e1")))
        super().hoverLeaveEvent(event)

class TaxonEdge(QGraphicsLineItem):
    def __init__(self, x1, y1, x2, y2, parent=None):
        super().__init__(x1, y1, x2, y2, parent)
        self.setPen(QPen(QColor("#a0aec0"), 1))

class TaxonomyScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.nodes = {}
        self.edges = []
        
    def clear_taxonomy(self):
        self.clear()
        self.nodes = {}
        self.edges = []

class TaxonomyVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.start_year = 1985
        self.end_year = 2004
        self.current_year = self.start_year
        self.init_ui()
        self.init_data()
        self.setup_animations()
        
       
    def init_data(self):
        # Tree definitions (similar to previous version)

        self.start_year = 1985
        self.end_year = 2004
        self.taxa_timeline = {
            "Root": 1985,
            "Mammalia": 1985,
            "Carnivora": 1985,
            "Felidae": 1985,
            "Panthera": 1985,
            "Felis": 1985,
            "Canidae": 1985,
            "Canis": 1985,
            "Vulpes": 1985,
            "Cetacea": 1985,
            "Delphinidae": 1985,
            "Artiodactyla": 1985,
            "Bovidae": 1985,
            "Bos": 1985,
            "Ovis": 1985,
            "Viverra": 1985,
            # New classifications
            "Feliformia": 1994,
            "Caniformia": 1994,
            "Viverridae": 2000,
            "Cetartiodactyla": 1997,
        }

        # Define the taxonomy trees
        self.tree1 = {
            "year": 1985,
            "author": "Smith et al.",
            "name": "Root",
            "children": [{
                "name": "Mammalia",
                "children": [
                    {
                        "name": "Carnivora",
                        "children": [
                            {
                                "name": "Felidae",
                                "children": [
                                    {"name": "Panthera"},
                                    {"name": "Felis"},
                                    {"name": "Viverra"}
                                ]
                            },
                            {
                                "name": "Canidae",
                                "children": [
                                    {"name": "Canis"},
                                    {"name": "Vulpes"}
                                ]
                            }
                        ]
                    },
                    {
                        "name": "Cetacea",
                        "children": [
                            {"name": "Delphinidae"}
                        ]
                    },
                    {
                        "name": "Artiodactyla",
                        "children": [
                            {
                                "name": "Bovidae",
                                "children": [
                                    {"name": "Bos"},
                                    {"name": "Ovis"}
                                ]
                            }
                        ]
                    }
                ]
            }]
        }

        self.tree2 = {
            "year": 2004,
            "author": "Johnson & Zhang",
            "name": "Root",
            "children": [{
                "name": "Mammalia",
                "children": [
                    {
                        "name": "Carnivora",
                        "children": [
                            {
                                "name": "Feliformia",
                                "children": [
                                    {
                                        "name": "Felidae",
                                        "children": [
                                            {"name": "Panthera"},
                                            {"name": "Felis"}
                                        ]
                                    },
                                    {
                                        "name": "Viverridae",
                                        "children": [
                                            {"name": "Viverra"}
                                        ]
                                    }
                                ]
                            },
                            {
                                "name": "Caniformia",
                                "children": [
                                    {
                                        "name": "Canidae",
                                        "children": [
                                            {"name": "Canis"},
                                            {"name": "Vulpes"}
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "name": "Cetartiodactyla",
                        "children": [
                            {
                                "name": "Cetacea",
                                "children": [{"name": "Delphinidae"}]
                            },
                            {
                                "name": "Bovidae",
                                "children": [
                                    {"name": "Bos"},
                                    {"name": "Ovis"}
                                ]
                            }
                        ]
                    }
                ]
            }]
        }

        # Define taxonomic events
        self.taxonomic_events = [
            {
                "year": 1985,
                "changes": [{
                    "taxa": ["Cetacea", "Artiodactyla"],
                    "explanation": "Traditional classification based on morphological differences separates whales (Cetacea) from even-toed ungulates (Artiodactyla)."
                }]
            },
            {
                "year": 1989,
                "changes": [{
                    "taxa": ["Viverra"],
                    "explanation": "Early molecular studies suggest closer relationship between Viverra and felids."
                }]
            },
            {
                "year": 1994,
                "changes": [{
                    "taxa": ["Carnivora"],
                    "explanation": "Morphological analysis reveals clear division between cat-like and dog-like carnivores."
                }]
            },
            {
                "year": 1997,
                "changes": [{
                    "taxa": ["Cetartiodactyla"],
                    "explanation": "Molecular studies suggest whales evolved from within Artiodactyla."
                }]
            },
            {
                "year": 2000,
                "changes": [{
                    "taxa": ["Viverridae"],
                    "explanation": "Combined analysis confirms Viverra belongs in separate family Viverridae."
                }]
            },
            {
                "year": 2004,
                "changes": [{
                    "taxa": ["Cetartiodactyla", "Feliformia", "Caniformia"],
                    "explanation": "Modern consensus classification incorporating molecular, morphological, and fossil evidence."
                }]
            }
        ]

        # Initialize visualization       
        self.calculate_positions()
        self.draw_taxonomy()

    def init_ui(self):
        self.setWindowTitle('Taxonomy Evolution Visualizer')
        self.setGeometry(100, 100, 1200, 800)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Year control
        year_layout = QHBoxLayout()
        self.year_label = QLabel(f"Year: {self.start_year}")
        self.year_slider = QSlider(Qt.Orientation.Horizontal)
        self.year_slider.setMinimum(self.start_year)
        self.year_slider.setMaximum(self.end_year)
        self.year_slider.setValue(self.start_year)
        self.year_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.year_slider.setTickInterval(1)
        year_layout.addWidget(self.year_label)
        year_layout.addWidget(self.year_slider)
        
        self.scene = TaxonomyScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.explanation = QTextEdit()
        self.explanation.setReadOnly(True)
        self.explanation.setMaximumHeight(150)
        
        layout.addLayout(year_layout)
        layout.addWidget(self.view)
        layout.addWidget(self.explanation)
        
        self.year_slider.valueChanged.connect(self.year_changed)

    def count_descendants(self, node):
        """Count total number of descendants for a node"""
        count = 1
        if "children" in node:
            for child in node["children"]:
                count += self.count_descendants(child)
        return count

    def get_tree_depth(self, node, current_depth=0):
        """Get maximum depth of the tree"""
        if "children" not in node or not node["children"]:
            return current_depth
        return max(self.get_tree_depth(child, current_depth + 1) 
                  for child in node["children"])
    def calculate_positions(self):
        def get_subtree_size(node):
            """Calculate the size of a subtree"""
            if "children" not in node or not node["children"]:
                return 1
            return sum(get_subtree_size(child) for child in node["children"])

        def calculate_tree_positions(node, level=0, offset=0, positions=None):
            if positions is None:
                positions = {}
            
            horizontal_spacing = 80  # Base spacing between nodes
            vertical_spacing = 80    # Spacing between levels
            
            # Calculate position for current node
            y = level * vertical_spacing
            x = offset * horizontal_spacing
            
            # Store position
            positions[node["name"]] = (x, y)
            
            if "children" in node and node["children"]:
                total_children = len(node["children"])
                # Calculate total width needed for children
                total_width = 0
                child_sizes = []
                
                for child in node["children"]:
                    size = get_subtree_size(child)
                    child_sizes.append(size)
                    total_width += size
                
                # Calculate starting position for first child
                start_x = x - (total_width - 1) * horizontal_spacing / 2
                
                # Position each child
                current_offset = 0
                for i, child in enumerate(node["children"]):
                    # Center child within its allocated space
                    child_offset = start_x/horizontal_spacing + current_offset + child_sizes[i]/2
                    calculate_tree_positions(child, level + 1, child_offset, positions)
                    current_offset += child_sizes[i]
            
            return positions

        # Calculate positions for both trees
        self.positions1 = calculate_tree_positions(self.tree1)
        self.positions2 = calculate_tree_positions(self.tree2)

        # Center the trees
        def center_positions(positions):
            if not positions:
                return
            
            min_x = min(x for x, y in positions.values())
            max_x = max(x for x, y in positions.values())
            center_offset = (max_x + min_x) / 2
            
            for node in positions:
                x, y = positions[node]
                positions[node] = (x - center_offset, y)
        
        center_positions(self.positions1)
        center_positions(self.positions2)

    def get_current_tree(self):
        """Get the appropriate tree structure based on the current year"""
        if self.current_year < 1994:
            return self.tree1
        elif self.current_year < 1997:
            # Create intermediate tree with Feliformia/Caniformia
            intermediate_tree = self.modify_tree_for_year(self.tree1, self.current_year)
            # Move Felidae and Canidae under their respective new parent groups
            if "children" in intermediate_tree:
                for mammalia in intermediate_tree["children"]:
                    if mammalia["name"] == "Mammalia":
                        for carnivora in mammalia["children"]:
                            if carnivora["name"] == "Carnivora":
                                carnivora["children"] = [
                                    {
                                        "name": "Feliformia",
                                        "children": [node for node in carnivora["children"] 
                                                   if node["name"] == "Felidae"]
                                    },
                                    {
                                        "name": "Caniformia",
                                        "children": [node for node in carnivora["children"]
                                                   if node["name"] == "Canidae"]
                                    }
                                ]
            return intermediate_tree
        else:
            return self.modify_tree_for_year(self.tree2, self.current_year)

    # ... (rest of the methods remain the same)



    def interpolate_positions(self, progress):
        positions = {}
        all_nodes = set(self.positions1.keys()) | set(self.positions2.keys())
        
        for node in all_nodes:
            if node in self.positions1 and node in self.positions2:
                x1, y1 = self.positions1[node]
                x2, y2 = self.positions2[node]
                x = x1 + (x2 - x1) * progress
                y = y1 + (y2 - y1) * progress
                positions[node] = (x, y)
            elif node in self.positions1:
                positions[node] = self.positions1[node]
            else:
                positions[node] = self.positions2[node]
        
        return positions

    def modify_tree_for_year(self, base_tree, year):
        """Modify tree structure based on the current year"""
        def filter_node(node):
            if node["name"] not in self.taxa_timeline:
                return True
            return self.taxa_timeline[node["name"]] <= year

        def process_node(node):
            if not filter_node(node):
                return None
            
            new_node = node.copy()
            if "children" in node:
                new_children = []
                for child in node["children"]:
                    processed_child = process_node(child)
                    if processed_child is not None:
                        new_children.append(processed_child)
                if new_children:
                    new_node["children"] = new_children
                elif "children" in new_node:
                    del new_node["children"]
            return new_node

        modified_tree = process_node(base_tree)
        return modified_tree if modified_tree else {"name": "Root"}

    def draw_taxonomy(self):
        self.scene.clear_taxonomy()
        
        current_tree = self.get_current_tree()
        progress = (self.current_year - self.start_year) / (self.end_year - self.start_year)
        positions = self.interpolate_positions(progress)
        
        # Draw edges first
        def draw_edges(node):
            if "children" in node:
                parent_pos = positions[node["name"]]
                for child in node["children"]:
                    child_pos = positions[child["name"]]
                    edge = TaxonEdge(parent_pos[0], parent_pos[1],
                                   child_pos[0], child_pos[1])
                    self.scene.addItem(edge)
                    self.scene.edges.append(edge)
                    draw_edges(child)
                    
        draw_edges(current_tree)
        
        # Draw only nodes that should exist at the current year
        for name, pos in positions.items():
            if name in self.taxa_timeline and self.taxa_timeline[name] <= self.current_year:
                node = TaxonNode(name, pos[0], pos[1])
                self.scene.addItem(node)
                self.scene.nodes[name] = node
        
        # Fit view to contents
        self.view.fitInView(self.scene.itemsBoundingRect().adjusted(-50, -50, 50, 50), 
                           Qt.AspectRatioMode.KeepAspectRatio)


    def setup_animations(self):
        self.animations = []

    def year_changed(self, year):
        self.current_year = year
        self.year_label.setText(f"Year: {year}")
        self.draw_taxonomy()
        self.update_explanation()
    
    def update_explanation(self):
        current_events = [event for event in self.taxonomic_events 
                         if event["year"] <= self.current_year]
        if current_events:
            latest_event = current_events[-1]
            explanation = f"Changes in {latest_event['year']}:\n\n"
            for change in latest_event["changes"]:
                explanation += f"Affected taxa: {', '.join(change['taxa'])}\n"
                explanation += f"{change['explanation']}\n\n"
        else:
            explanation = "No changes yet."
            
        self.explanation.setText(explanation)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.draw_taxonomy()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look across platforms
    vis = TaxonomyVisualizer()
    vis.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
