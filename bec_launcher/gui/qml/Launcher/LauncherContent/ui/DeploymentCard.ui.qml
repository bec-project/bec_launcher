/*
  DeploymentCard.ui.qml - Qt Design Studio compatible UI form
  A card showing deployment info with selection capability
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Launcher

Rectangle {
    id: root
    width: 400
    height: contentColumn.implicitHeight + 24

    // ─────────────────────────────────────────────────────────
    // Properties (inputs)
    // ─────────────────────────────────────────────────────────
    property string deploymentName: "SLS2-prod"
    property string deploymentPath: ""
    property string badgeType: "prod"  // "prod", "test", "dev"
    property bool isSelected: false
    property bool isHovered: false

    // ─────────────────────────────────────────────────────────
    // Signals (outputs)
    // ─────────────────────────────────────────────────────────
    signal clicked()

    radius: Theme.radiusMedium
    color: root.isSelected ? Theme.backgroundCardSelected
         : root.isHovered ? Theme.backgroundCardHover
         : Theme.backgroundCard
    border.width: root.isSelected ? 2 : 1
    border.color: root.isSelected ? Theme.borderSelected
                : root.isHovered ? Theme.borderHover
                : Theme.border

    ColumnLayout {
        id: contentColumn
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                Text {
                    text: root.deploymentName
                    color: Theme.textPrimary
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                }

                Text {
                    text: root.deploymentPath
                    color: Theme.textMuted
                    font.pixelSize: 11
                    elide: Text.ElideMiddle
                    Layout.fillWidth: true
                }
            }

            // Badge
            Rectangle {
                Layout.preferredWidth: badgeText.implicitWidth + 16
                Layout.preferredHeight: 22
                radius: 11
                color: root.badgeType === "prod" ? Theme.badgeProdBg
                     : root.badgeType === "test" ? Theme.badgeTestBg
                     : Theme.badgeDevBg
                border.width: 1
                border.color: root.badgeType === "prod" ? Theme.badgeProd
                            : root.badgeType === "test" ? Theme.badgeTest
                            : Theme.badgeDev

                Text {
                    id: badgeText
                    anchors.centerIn: parent
                    text: root.badgeType.toUpperCase()
                    color: root.badgeType === "prod" ? Theme.badgeProd
                         : root.badgeType === "test" ? Theme.badgeTest
                         : Theme.badgeDev
                    font.pixelSize: 10
                    font.weight: Font.Bold
                }
            }

            // Checkmark for selected
            Text {
                visible: root.isSelected
                text: "✓"
                color: Theme.accent
                font.pixelSize: 16
                font.weight: Font.Bold
            }
        }
    }

    // MouseArea for interaction - signal handlers connected externally
    property alias cardMouseArea: cardMouseArea

    MouseArea {
        id: cardMouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
    }
}
