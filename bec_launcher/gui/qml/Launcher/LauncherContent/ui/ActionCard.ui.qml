/*
  ActionCard.ui.qml - Qt Design Studio compatible UI form
  A card for launching GUI or Terminal
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
    property string title: "Terminal"
    property string description: "Open a terminal session"
    property string icon: "▶"
    property string buttonText: "Launch"
    property bool isHovered: false

    // ─────────────────────────────────────────────────────────
    // Signals (outputs)
    // ─────────────────────────────────────────────────────────
    signal launched()

    radius: Theme.radiusMedium
    color: root.isHovered ? Theme.backgroundCardHover : Theme.backgroundCard
    border.width: 1
    border.color: root.isHovered ? Theme.borderHover : Theme.border

    ColumnLayout {
        id: contentColumn
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            // Icon circle
            Rectangle {
                Layout.preferredWidth: 40
                Layout.preferredHeight: 40
                radius: 20
                color: Theme.accent
                opacity: 0.15

                Text {
                    anchors.centerIn: parent
                    text: root.icon
                    color: Theme.accent
                    font.pixelSize: 18
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Text {
                    text: root.title
                    color: Theme.textPrimary
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                }

                Text {
                    text: root.description
                    color: Theme.textSecondary
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }

        Button {
            id: launchButton
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            text: root.buttonText

            contentItem: Text {
                text: launchButton.text
                color: Theme.textPrimary
                font.pixelSize: 13
                font.weight: Font.DemiBold
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }

            background: Rectangle {
                radius: Theme.radiusSmall
                color: launchButton.pressed ? Theme.accentPressed
                     : launchButton.hovered ? Theme.accentHover
                     : Theme.accent
            }
        }
    }

    // Expose button and mouseArea for external signal connection
    property alias launchButton: launchButton
    property alias cardMouseArea: cardMouseArea

    MouseArea {
        id: cardMouseArea
        anchors.fill: parent
        hoverEnabled: true
        propagateComposedEvents: true
        acceptedButtons: Qt.NoButton
    }
}
