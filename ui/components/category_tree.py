"""
Category and Item Tree widget with tri-state checkboxes, risk badges, and i18n support.
"""

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QHeaderView
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QFont
from typing import Dict, List, Optional
from core.models import ScanItem, CategoryGroup, Category, RiskLevel, format_bytes
from core.i18n import t


class CategoryTreeWidget(QTreeWidget):
    """Hierarchical tree showing categories and cleanable items with checkboxes and risk badges."""

    selection_changed_signal = Signal()
    item_focused_signal = Signal(object) # emits ScanItem

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_tree()
        self._items_map: Dict[QTreeWidgetItem, ScanItem] = {}
        self._category_nodes: Dict[Category, QTreeWidgetItem] = {}
        self._block_signals = False

    def _init_tree(self):
        self.setColumnCount(4)
        self.setHeaderLabels([
            t("tree_col_category"),
            t("tree_col_risk"),
            t("tree_col_size"),
            t("tree_col_files")
        ])

        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.setAnimated(True)
        self.setIndentation(22)
        self.itemChanged.connect(self._on_item_changed)
        self.itemClicked.connect(self._on_item_clicked)
        self.currentItemChanged.connect(self._on_current_changed)

    def populate(self, category_groups: Dict[Category, CategoryGroup]):
        self._block_signals = True
        self.clear()
        self._items_map.clear()
        self._category_nodes.clear()

        # Update header labels in case language changed
        self.setHeaderLabels([
            t("tree_col_category"),
            t("tree_col_risk"),
            t("tree_col_size"),
            t("tree_col_files")
        ])

        for category, group in category_groups.items():
            if not group.items:
                continue

            # Category Parent Node
            cat_node = QTreeWidgetItem(self)
            cat_node.setText(0, f"{category.icon_name}  {category.display_name}")
            cat_node.setFont(0, QFont("Segoe UI", 10, QFont.Bold))
            cat_node.setText(2, format_bytes(group.total_size))
            cat_node.setText(3, str(sum(i.file_count for i in group.items)))
            cat_node.setFlags(cat_node.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)

            self._category_nodes[category] = cat_node

            has_selected = False
            has_unselected = False

            for item in group.items:
                item_node = QTreeWidgetItem(cat_node)
                item_node.setText(0, item.title)
                item_node.setText(1, item.risk_level.badge_text)
                item_node.setText(2, item.format_size())
                item_node.setText(3, str(item.file_count))

                # Color risk text
                item_node.setForeground(1, QBrush(QColor(item.risk_level.color_hex)))

                item_node.setFlags(item_node.flags() | Qt.ItemIsUserCheckable)
                check_state = Qt.Checked if item.is_selected else Qt.Unchecked
                item_node.setCheckState(0, check_state)

                if item.is_selected:
                    has_selected = True
                else:
                    has_unselected = True

                self._items_map[item_node] = item

            # Set category checkbox state
            if has_selected and not has_unselected:
                cat_node.setCheckState(0, Qt.Checked)
            elif has_selected and has_unselected:
                cat_node.setCheckState(0, Qt.PartiallyChecked)
            else:
                cat_node.setCheckState(0, Qt.Unchecked)

            cat_node.setExpanded(True)

        self._block_signals = False
        self.selection_changed_signal.emit()

    def _on_item_changed(self, tree_item: QTreeWidgetItem, column: int):
        if self._block_signals or column != 0:
            return

        if tree_item in self._items_map:
            scan_item = self._items_map[tree_item]
            scan_item.is_selected = (tree_item.checkState(0) == Qt.Checked)
            self._update_parent_category(tree_item.parent())
            self.selection_changed_signal.emit()

        elif tree_item.childCount() > 0:
            state = tree_item.checkState(0)
            if state != Qt.PartiallyChecked:
                self._block_signals = True
                for i in range(tree_item.childCount()):
                    child = tree_item.child(i)
                    child.setCheckState(0, state)
                    if child in self._items_map:
                        self._items_map[child].is_selected = (state == Qt.Checked)
                self._block_signals = False
                self.selection_changed_signal.emit()

    def _update_parent_category(self, parent_node: Optional[QTreeWidgetItem]):
        if not parent_node:
            return
        total_children = parent_node.childCount()
        checked_count = sum(1 for i in range(total_children) if parent_node.child(i).checkState(0) == Qt.Checked)

        self._block_signals = True
        if checked_count == total_children:
            parent_node.setCheckState(0, Qt.Checked)
        elif checked_count > 0:
            parent_node.setCheckState(0, Qt.PartiallyChecked)
        else:
            parent_node.setCheckState(0, Qt.Unchecked)
        self._block_signals = False

    def _on_item_clicked(self, tree_item: QTreeWidgetItem, column: int):
        if tree_item in self._items_map:
            self.item_focused_signal.emit(self._items_map[tree_item])

    def _on_current_changed(self, current: Optional[QTreeWidgetItem], previous: Optional[QTreeWidgetItem]):
        if current and current in self._items_map:
            self.item_focused_signal.emit(self._items_map[current])

    def select_all_safe(self):
        self._block_signals = True
        for node, item in self._items_map.items():
            if item.risk_level == RiskLevel.SAFE:
                node.setCheckState(0, Qt.Checked)
                item.is_selected = True
            else:
                node.setCheckState(0, Qt.Unchecked)
                item.is_selected = False

        for cat_node in self._category_nodes.values():
            self._update_parent_category(cat_node)

        self._block_signals = False
        self.selection_changed_signal.emit()

    def select_all(self, select: bool = True):
        self._block_signals = True
        state = Qt.Checked if select else Qt.Unchecked
        for node, item in self._items_map.items():
            node.setCheckState(0, state)
            item.is_selected = select

        for cat_node in self._category_nodes.values():
            cat_node.setCheckState(0, state)

        self._block_signals = False
        self.selection_changed_signal.emit()

    def get_selected_items(self) -> List[ScanItem]:
        return [item for item in self._items_map.values() if item.is_selected]
