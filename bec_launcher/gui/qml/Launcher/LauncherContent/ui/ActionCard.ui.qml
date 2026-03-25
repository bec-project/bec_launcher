import QtQuick
import QtQuick.Controls
import Launcher

Rectangle {
    id: root
    width: 400
    height: Constants.actionCardHeight

    property string actionId: "terminal"
    property string title: "Terminal"
    property string description: "Open a terminal session"
    property string icon: "▶"
    property url iconSource: ""
    property string buttonText: "Launch"
    property bool isDefault: false
    property bool isHovered: false

    radius: Theme.radiusMedium
    color: root.isDefault ? Theme.backgroundCardDefault
        : root.isHovered ? Theme.backgroundCardHover
            : Theme.backgroundCard
    border.width: 1
    border.color: root.isDefault ? Theme.borderDefault
        : root.isHovered ? Theme.borderHover
            : Theme.border

    Column {
        anchors.fill: parent
        anchors.margins: Constants.actionCardPadding
        spacing: Constants.actionCardButtonGap

        Item {
            id: contentArea
            width: parent.width
            height: parent.height - launchButton.height - parent.spacing
            clip: true

            MouseArea {
                id: cardMouseArea
                anchors.fill: parent
                z: -1
                hoverEnabled: true
                propagateComposedEvents: true
                acceptedButtons: Qt.LeftButton
            }

            Row {
                id: contentRow
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

                Item {
                    width: parent.width - Constants.actionCardIconSize - Constants.actionCardGap
                    height: titleRow.height + 4 + descriptionText.contentHeight

                    Row {
                        id: titleRow
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.right: parent.right
                        spacing: 8

                        Text {
                            id: titleText
                            width: parent.width - defaultToggle.width - parent.spacing
                            height: Constants.actionCardTitleHeight
                            text: root.title
                            color: Theme.textPrimary
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                            verticalAlignment: Text.AlignTop
                            elide: Text.ElideRight
                        }

                        Rectangle {
                            id: defaultToggle
                            width: root.isDefault ? defaultToggleLabel.implicitWidth + 16 : Constants.defaultToggleHeight
                            height: Constants.defaultToggleHeight
                            radius: height / 2
                            color: root.isDefault ? Theme.accent : Theme.buttonSecondary
                            border.width: 1
                            border.color: root.isDefault ? Theme.accent : Theme.border

                            Text {
                                id: defaultToggleLabel
                                anchors.centerIn: parent
                                text: root.isDefault ? "Default" : "☆"
                                color: Theme.textPrimary
                                font.pixelSize: root.isDefault ? 10 : 12
                                font.weight: Font.DemiBold
                            }

                            MouseArea {
                                id: defaultToggleMouseArea
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                            }
                        }
                    }

                    Text {
                        id: descriptionText
                        anchors.top: titleRow.bottom
                        anchors.topMargin: 4
                        anchors.left: parent.left
                        anchors.right: parent.right
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
    property alias defaultToggleMouseArea: defaultToggleMouseArea
}
