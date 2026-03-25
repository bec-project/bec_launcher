import QtQuick
import QtQuick.Layouts
import Launcher

Rectangle {
    id: root
    width: 400
    height: contentColumn.implicitHeight + (Constants.deploymentCardPadding * 2)

    property string deploymentName: "SLS2-prod"
    property string deploymentPath: ""
    property string badgeType: "prod"
    property bool isSelected: false
    property bool isDefault: false
    property bool isHovered: false

    radius: Theme.radiusMedium
    color: root.isSelected && root.isDefault ? Theme.backgroundCardSelectedDefault
        : root.isSelected ? Theme.backgroundCardSelected
            : root.isDefault ? Theme.backgroundCardDefault
         : root.isHovered ? Theme.backgroundCardHover
         : Theme.backgroundCard
    border.width: root.isSelected ? 2 : 1
    border.color: root.isSelected ? Theme.borderSelected
                : root.isHovered ? Theme.borderHover
                : Theme.border

    ColumnLayout {
        id: contentColumn
        anchors.fill: parent
        anchors.margins: Constants.deploymentCardPadding
        spacing: Constants.deploymentCardGap

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

            Rectangle {
                id: defaultToggle
                Layout.preferredWidth: defaultToggleLabel.implicitWidth + 16
                Layout.preferredHeight: Constants.defaultToggleHeight
                radius: height / 2
                color: root.isDefault ? Theme.accent : Theme.buttonSecondary
                border.width: 1
                border.color: root.isDefault ? Theme.accent : Theme.border

                Text {
                    id: defaultToggleLabel
                    anchors.centerIn: parent
                    text: "Default"
                    color: Theme.textPrimary
                    font.pixelSize: 10
                    font.weight: Font.DemiBold
                }

                MouseArea {
                    id: defaultToggleMouseArea
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                }
            }

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

            Text {
                visible: root.isSelected
                text: "✓"
                color: Theme.accent
                font.pixelSize: 16
                font.weight: Font.Bold
            }
        }
    }

    property alias cardMouseArea: cardMouseArea
    property alias defaultToggleMouseArea: defaultToggleMouseArea

    MouseArea {
        id: cardMouseArea
        anchors.fill: parent
        z: -1
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
    }
}
