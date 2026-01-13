pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import Launcher
import "ui"

Rectangle {
    id: root
    width: Constants.windowWidth
    color: Theme.background
    implicitWidth: Constants.windowWidth
    implicitHeight: root.pageContentHeight

    property var deploymentNames: []
    property var deploymentPaths: []
    property int selectedIndex: -1
    property bool deploymentConfirmed: false
    property bool rememberChoice: false

    signal deploymentSelected(int index)
    signal confirmDeployment()
    signal changeDeployment()
    signal launchTerminal()
    signal launchDock()
    signal launchApp()
    signal rememberChoiceToggled(bool checked)

    state: root.deploymentConfirmed ? "selectAction" : "selectDeployment"

    readonly property real collapsedHeight: (Constants.sectionPadding * 2) + Constants.sectionHeaderHeight
    readonly property real actionCardsHeight: Constants.stepLabelHeight
        + Constants.sectionGap
        + Constants.actionCardHeight
        + Constants.sectionGap
        + Constants.checkboxRowHeight
    readonly property real deploymentCardHeight: deploymentRepeater.count > 0 && deploymentRepeater.itemAt(0)
        ? deploymentRepeater.itemAt(0).height
        : 0
    readonly property real deploymentListContentHeight: deploymentListColumn.implicitHeight
    readonly property real deploymentViewportCapHeight: root.deploymentCardHeight > 0
        ? (Constants.deploymentListVisibleCount * root.deploymentCardHeight)
            + (Math.max(Constants.deploymentListVisibleCount - 1, 0) * Constants.deploymentCardGap)
        : 0
    readonly property real actionSectionVisibleHeight: root.deploymentConfirmed ? root.actionCardsHeight : 0
    readonly property real actionSectionGap: root.deploymentConfirmed ? Constants.sectionGap : 0
    readonly property real deploymentViewportHeight: root.deploymentConfirmed
        ? 0
        : Math.min(root.deploymentListContentHeight, root.deploymentViewportCapHeight)
    readonly property real deploymentSectionHeight: root.deploymentConfirmed
        ? root.collapsedHeight
        : root.collapsedHeight
            + (Constants.sectionGap * 3)
            + Constants.dividerThickness
            + root.deploymentViewportHeight
            + Constants.primaryButtonHeight
    readonly property real pageContentHeight: (Constants.pageMargin * 2)
        + Constants.headerHeight
        + Constants.dividerThickness
        + (Constants.sectionGap * 2)
        + root.deploymentSectionHeight
        + root.actionSectionGap
        + root.actionSectionVisibleHeight

    property alias changeButton: changeButton
    property alias confirmButton: confirmButton
    property alias terminalCard: terminalCard
    property alias dockCard: dockCard
    property alias appCard: appCard
    property alias deploymentRepeater: deploymentRepeater
    property alias rememberCheckbox: rememberCheckbox

    states: [
        State {
            name: "selectDeployment"
            PropertyChanges { deploymentSection.height: root.deploymentSectionHeight }
            PropertyChanges { deploymentListDivider.opacity: 1.0 }
            PropertyChanges {
                deploymentListWrapper.height: root.deploymentViewportHeight
                deploymentListWrapper.opacity: 1.0
            }
            PropertyChanges { confirmButton.opacity: 1.0 }
            PropertyChanges {
                actionSection.height: 0
                actionSection.opacity: 0.0
            }
        },
        State {
            name: "selectAction"
            PropertyChanges { deploymentSection.height: root.collapsedHeight }
            PropertyChanges { deploymentListDivider.opacity: 0.0 }
            PropertyChanges {
                deploymentListWrapper.height: 0
                deploymentListWrapper.opacity: 0.0
            }
            PropertyChanges { confirmButton.opacity: 0.0 }
            PropertyChanges {
                actionSection.height: root.actionCardsHeight
                actionSection.opacity: 1.0
            }
        }
    ]

    transitions: [
        Transition {
            from: "selectDeployment"
            to: "selectAction"
            SequentialAnimation {
                NumberAnimation {
                    targets: [deploymentSection, deploymentListDivider, deploymentListWrapper, confirmButton]
                    properties: "height,opacity"
                    duration: 220
                    easing.type: Easing.InCubic
                }
                NumberAnimation {
                    target: actionSection
                    properties: "height,opacity"
                    duration: 240
                    easing.type: Easing.OutCubic
                }
            }
        },
        Transition {
            from: "selectAction"
            to: "selectDeployment"
            SequentialAnimation {
                NumberAnimation {
                    target: actionSection
                    properties: "height,opacity"
                    duration: 180
                    easing.type: Easing.InCubic
                }
                NumberAnimation {
                    targets: [deploymentSection, deploymentListDivider, deploymentListWrapper, confirmButton]
                    properties: "height,opacity"
                    duration: 240
                    easing.type: Easing.OutCubic
                }
            }
        }
    ]

    Column {
        id: pageColumn
        anchors.fill: parent
        anchors.margins: Constants.pageMargin
        spacing: Constants.sectionGap

        Rectangle {
            id: headerRow
            width: parent.width
            height: Constants.headerHeight
            color: "transparent"

            Text {
                text: "BEC Launcher"
                color: Theme.textPrimary
                font.pixelSize: 22
                font.weight: Font.Bold
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        Rectangle {
            width: parent.width
            height: Constants.dividerThickness
            color: Theme.divider
        }

        Rectangle {
            id: deploymentSection
            width: parent.width
            height: root.deploymentSectionHeight
            radius: Constants.sectionRadius
            color: Theme.backgroundCard
            border.width: 1
            border.color: Theme.border
            clip: true

            Column {
                id: deploymentContent
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: Constants.sectionPadding
                spacing: Constants.sectionGap

                Rectangle {
                    id: deploymentHeader
                    width: parent.width
                    height: Constants.sectionHeaderHeight
                    color: "transparent"

                    Column {
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.right: headerButtons.left
                        anchors.rightMargin: 10
                        spacing: 2

                        Text {
                            text: root.deploymentConfirmed ? "Selected Deployment" : "Step 1: Select Deployment"
                            color: Theme.textSecondary
                            font.pixelSize: 11
                            font.weight: Font.Medium
                        }

                        Text {
                            text: root.selectedIndex >= 0 && root.selectedIndex < root.deploymentNames.length
                                  ? root.deploymentNames[root.selectedIndex]
                                  : "Choose a deployment..."
                            color: Theme.textPrimary
                            font.pixelSize: 15
                            font.weight: Font.DemiBold
                        }
                    }

                    Row {
                        id: headerButtons
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 8

                        Button {
                            id: changeButton
                            visible: root.deploymentConfirmed
                            enabled: root.deploymentNames.length > 1
                            width: Constants.changeButtonWidth
                            height: Constants.smallButtonHeight
                            text: "Change"

                            ToolTip.visible: !changeButton.enabled && changeButton.hovered
                            ToolTip.text: "There is only one deployment available."

                            contentItem: Text {
                                text: changeButton.text
                                color: changeButton.enabled ? Theme.textPrimary : Theme.textDisabled
                                font.pixelSize: 12
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }

                            background: Rectangle {
                                radius: 6
                                color: !changeButton.enabled ? Theme.buttonSecondary
                                     : changeButton.pressed ? Theme.buttonSecondaryHover
                                     : changeButton.hovered ? Theme.buttonSecondaryHover
                                     : Theme.buttonSecondary
                                opacity: changeButton.enabled ? 1.0 : 0.6
                                border.width: 1
                                border.color: Theme.border
                            }
                        }

                        Text {
                            text: root.deploymentConfirmed ? "▸" : "▾"
                            color: Theme.textMuted
                            font.pixelSize: 14
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }

                Rectangle {
                    id: deploymentListDivider
                    width: parent.width
                    height: Constants.dividerThickness
                    color: Theme.divider
                    opacity: 1.0
                    visible: opacity > 0
                }

                ScrollView {
                    id: deploymentListWrapper
                    width: parent.width
                    height: root.deploymentViewportHeight
                    clip: true
                    opacity: 1.0
                    visible: height > 0
                    contentWidth: availableWidth

                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    ScrollBar.vertical.policy: root.deploymentListContentHeight > root.deploymentViewportHeight
                        ? ScrollBar.AsNeeded
                        : ScrollBar.AlwaysOff

                    Column {
                        id: deploymentListColumn
                        width: deploymentListWrapper.availableWidth
                        spacing: Constants.deploymentCardGap

                        Repeater {
                            id: deploymentRepeater
                            model: root.deploymentNames

                            delegate: DeploymentCard {
                                required property int index
                                required property string modelData

                                width: deploymentListColumn.width
                                deploymentName: modelData
                                deploymentPath: index < root.deploymentPaths.length ? root.deploymentPaths[index] : ""
                                badgeType: modelData.toLowerCase().indexOf("test") >= 0 ? "test"
                                         : modelData.toLowerCase().indexOf("dev") >= 0 ? "dev"
                                         : "prod"
                                isSelected: index === root.selectedIndex
                            }
                        }
                    }
                }

                Button {
                    id: confirmButton
                    width: parent.width
                    height: Constants.primaryButtonHeight
                    text: "Confirm Selection"
                    enabled: root.selectedIndex >= 0
                    opacity: 1.0
                    visible: opacity > 0

                    contentItem: Text {
                        text: confirmButton.text
                        color: confirmButton.enabled ? Theme.textPrimary : Theme.textDisabled
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    background: Rectangle {
                        radius: 6
                        color: confirmButton.enabled
                               ? (confirmButton.pressed ? Theme.accentPressed
                                  : confirmButton.hovered ? Theme.accentHover
                                  : Theme.accent)
                               : Theme.buttonSecondary
                        opacity: confirmButton.enabled ? 1.0 : 0.5
                    }
                }
            }
        }

        Rectangle {
            id: actionSection
            width: parent.width
            height: 0
            color: "transparent"
            opacity: 0.0
            visible: height > 0
            clip: true

            Column {
                anchors.fill: parent
                spacing: Constants.sectionGap

                Text {
                    text: "Step 2: Choose App Environment"
                    height: Constants.stepLabelHeight
                    color: Theme.textSecondary
                    font.pixelSize: 11
                    font.weight: Font.Medium
                }

                Row {
                    width: parent.width
                    height: Constants.actionCardHeight
                    spacing: Constants.actionCardGap

                    ActionCard {
                        id: terminalCard
                        width: (parent.width - (Constants.actionCardGap * 2)) / 3
                        height: Constants.actionCardHeight
                        title: "Terminal"
                        description: "Open BEC in terminal without a graphical user interface."
                        icon: ">"
                        iconSource: Qt.resolvedUrl("images/BEC_terminal.png")
                        buttonText: "Open Terminal"
                    }

                    ActionCard {
                        id: dockCard
                        width: (parent.width - (Constants.actionCardGap * 2)) / 3
                        height: Constants.actionCardHeight
                        title: "Terminal + Dock"
                        description: "Open BEC in terminal with the GUI dock area companion window."
                        icon: "#"
                        iconSource: Qt.resolvedUrl("images/BEC_comp.png")
                        buttonText: "Open Terminal + Dock"
                    }

                    ActionCard {
                        id: appCard
                        width: (parent.width - (Constants.actionCardGap * 2)) / 3
                        height: Constants.actionCardHeight
                        title: "BEC App"
                        description: "Fully fledged BEC desktop application environment."
                        icon: "[]"
                        iconSource: Qt.resolvedUrl("images/BEC_app.png")
                        buttonText: "Launch BEC App"
                    }
                }

                Rectangle {
                    width: parent.width
                    height: Constants.checkboxRowHeight
                    color: "transparent"

                    CheckBox {
                        id: rememberCheckbox
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        checked: root.rememberChoice
                        text: "Remember my choice (skip this screen next time)"

                        contentItem: Text {
                            text: rememberCheckbox.text
                            color: Theme.textSecondary
                            font.pixelSize: 12
                            leftPadding: rememberCheckbox.indicator.width + rememberCheckbox.spacing
                            verticalAlignment: Text.AlignVCenter
                        }

                        indicator: Rectangle {
                            implicitWidth: Constants.checkboxIndicatorSize
                            implicitHeight: Constants.checkboxIndicatorSize
                            x: rememberCheckbox.leftPadding
                            y: (parent.height - height) / 2
                            radius: 4
                            color: rememberCheckbox.checked ? Theme.accent : Theme.backgroundInput
                            border.color: rememberCheckbox.checked ? Theme.accent : Theme.border
                            border.width: 1

                            Text {
                                anchors.centerIn: parent
                                text: "✓"
                                color: Theme.textPrimary
                                font.pixelSize: 12
                                font.weight: Font.Bold
                                visible: rememberCheckbox.checked
                            }
                        }
                    }
                }
            }
        }
    }
}
