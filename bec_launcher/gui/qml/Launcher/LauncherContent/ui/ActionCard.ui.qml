import QtQuick
import QtQuick.Controls
import Launcher

Rectangle {
    id: root
    width: 400
    height: Constants.actionCardHeight

    property string title: "Terminal"
    property string description: "Open a terminal session"
    property string icon: "▶"
    property url iconSource: ""
    property string buttonText: "Launch"
    property bool isHovered: false

    radius: Theme.radiusMedium
    color: root.isHovered ? Theme.backgroundCardHover : Theme.backgroundCard
    border.width: 1
    border.color: root.isHovered ? Theme.borderHover : Theme.border

    Column {
        anchors.fill: parent
        anchors.margins: Constants.actionCardPadding
        spacing: Constants.actionCardButtonGap

        Item {
            width: parent.width
            height: parent.height - launchButton.height - parent.spacing
            clip: true

            Row {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                spacing: Constants.actionCardGap

                Item {
                    width: Constants.actionCardIconSize
                    height: Constants.actionCardIconSize

                    Image {
                        anchors.fill: parent
                        source: root.iconSource
                        fillMode: Image.PreserveAspectFit
                        visible: root.iconSource !== ""
                    }

                    Text {
                        anchors.fill: parent
                        text: root.icon
                        color: Theme.accent
                        font.pixelSize: 18
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        visible: root.iconSource === ""
                    }
                }

                Column {
                    width: parent.width - Constants.actionCardIconSize - Constants.actionCardGap
                    spacing: 2

                    Text {
                        width: parent.width
                        height: Constants.actionCardTitleHeight
                        text: root.title
                        color: Theme.textPrimary
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                        verticalAlignment: Text.AlignTop
                    }

                    Text {
                        width: parent.width
                        text: root.description
                        color: Theme.textSecondary
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                        verticalAlignment: Text.AlignTop
                    }
                }
            }
        }

        Button {
            id: launchButton
            width: parent.width
            height: Constants.actionCardButtonHeight
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
