/*
  AppForm.ui.qml - Qt Design Studio compatible UI form
  Main application layout with deployment selection and action cards

  NOTE: This file is purely declarative for Qt Design Studio compatibility.
  Signal handlers are connected in App.qml

  States:
  - "selectDeployment": Initial state, user selects a deployment
  - "selectAction": Deployment confirmed, user selects Terminal or GUI
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Launcher
import "ui"

Rectangle {
    id: root
    width: Constants.width
    height: Constants.height
    color: Theme.background

    // ─────────────────────────────────────────────────────────
    // Properties (inputs from backend)
    // ─────────────────────────────────────────────────────────
    property var deploymentNames: []
    property var deploymentPaths: []
    property int selectedIndex: -1
    property bool deploymentConfirmed: false
    property string appVersion: "0.0.0"
    property bool rememberChoice: false

    // ─────────────────────────────────────────────────────────
    // Signals (outputs to backend)
    // ─────────────────────────────────────────────────────────
    signal deploymentSelected(int index)
    signal confirmDeployment()
    signal changeDeployment()
    signal launchTerminal()
    signal launchGui()
    signal rememberChoiceToggled(bool checked)

    // ─────────────────────────────────────────────────────────
    // QML States for Qt Design Studio
    // ─────────────────────────────────────────────────────────
    state: root.deploymentConfirmed ? "selectAction" : "selectDeployment"

    states: [
        State {
            name: "selectDeployment"
            PropertyChanges {
                target: deploymentSection
                height: root.collapsedHeight + root.expandedListHeight + 12
            }
            PropertyChanges {
                target: deploymentListWrapper
                height: deploymentListColumn.implicitHeight
                opacity: 1.0
            }
            PropertyChanges {
                target: actionSection
                height: 0
                opacity: 0.0
            }
        },
        State {
            name: "selectAction"
            PropertyChanges {
                target: deploymentSection
                height: root.collapsedHeight
            }
            PropertyChanges {
                target: deploymentListWrapper
                height: 0
                opacity: 0.0
            }
            PropertyChanges {
                target: actionSection
                height: root.actionCardsHeight
                opacity: 1.0
            }
        }
    ]

    transitions: [
        Transition {
            from: "selectDeployment"
            to: "selectAction"
            SequentialAnimation {
                NumberAnimation {
                    targets: [deploymentSection, deploymentListWrapper]
                    properties: "height,opacity"
                    duration: 280
                    easing.type: Easing.OutCubic
                }
                NumberAnimation {
                    target: actionSection
                    properties: "height,opacity"
                    duration: 280
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
                    duration: 200
                    easing.type: Easing.InCubic
                }
                NumberAnimation {
                    targets: [deploymentSection, deploymentListWrapper]
                    properties: "height,opacity"
                    duration: 280
                    easing.type: Easing.OutCubic
                }
            }
        }
    ]

    // ─────────────────────────────────────────────────────────
    // Internal properties
    // ─────────────────────────────────────────────────────────
    property real collapsedHeight: 56
    property real expandedListHeight: deploymentListColumn.implicitHeight
    property real actionCardsHeight: 230

    // ─────────────────────────────────────────────────────────
    // Expose internal components for signal connection in App.qml
    // ─────────────────────────────────────────────────────────
    property alias changeButton: changeButton
    property alias confirmButton: confirmButton
    property alias terminalCard: terminalCard
    property alias guiCard: guiCard
    property alias deploymentRepeater: deploymentRepeater
    property alias rememberCheckbox: rememberCheckbox

    // Main content column
    Column {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        // ─────────────────────────────────────────────────────────
        // Header
        // ─────────────────────────────────────────────────────────
        Rectangle {
            id: headerRow
            width: parent.width
            height: 30
            color: "transparent"

            Text {
                text: "BEC Launcher"
                color: Theme.textPrimary
                font.pixelSize: 22
                font.weight: Font.Bold
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
            }

            Text {
                text: "v" + root.appVersion
                color: Theme.textMuted
                font.pixelSize: 12
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        Rectangle {
            width: parent.width
            height: 1
            color: Theme.divider
        }

        // ─────────────────────────────────────────────────────────
        // Step 1: Deployment Selection (collapsible)
        // ─────────────────────────────────────────────────────────
        Rectangle {
            id: deploymentSection
            width: parent.width
            height: root.collapsedHeight + root.expandedListHeight + 12
            radius: 14
            color: Theme.backgroundCard
            border.width: 1
            border.color: Theme.border
            clip: true

            Column {
                id: deploymentContent
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 12
                spacing: 12

                // Header (always visible)
                Rectangle {
                    id: deploymentHeader
                    width: parent.width
                    height: 32
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

                        // Change button (only when confirmed)
                        Button {
                            id: changeButton
                            visible: root.deploymentConfirmed
                            width: 80
                            height: 32
                            text: "Change"

                            contentItem: Text {
                                text: parent.text
                                color: Theme.textPrimary
                                font.pixelSize: 12
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }

                            background: Rectangle {
                                radius: 6
                                color: parent.pressed ? Theme.buttonSecondaryHover
                                     : parent.hovered ? Theme.buttonSecondaryHover
                                     : Theme.buttonSecondary
                                border.width: 1
                                border.color: Theme.border
                            }
                        }

                        // Expand/collapse indicator
                        Text {
                            text: root.deploymentConfirmed ? "▸" : "▾"
                            color: Theme.textMuted
                            font.pixelSize: 14
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }

                // Deployment list (animated visibility)
                Rectangle {
                    id: deploymentListWrapper
                    width: parent.width
                    height: deploymentListColumn.implicitHeight
                    color: "transparent"
                    clip: true
                    opacity: 1.0
                    visible: height > 0

                    Column {
                        id: deploymentListColumn
                        width: parent.width
                        spacing: 8

                        Rectangle {
                            width: parent.width
                            height: 1
                            color: Theme.divider
                        }

                        Repeater {
                            id: deploymentRepeater
                            model: root.deploymentNames

                            DeploymentCard {
                                width: deploymentListColumn.width
                                deploymentName: modelData
                                deploymentPath: index < root.deploymentPaths.length ? root.deploymentPaths[index] : ""
                                badgeType: modelData.toLowerCase().indexOf("test") >= 0 ? "test"
                                         : modelData.toLowerCase().indexOf("dev") >= 0 ? "dev"
                                         : "prod"
                                isSelected: index === root.selectedIndex
                            }
                        }

                        // Confirm button
                        Button {
                            id: confirmButton
                            width: parent.width
                            height: 40
                            text: "Confirm Selection"
                            enabled: root.selectedIndex >= 0

                            contentItem: Text {
                                text: parent.text
                                color: parent.enabled ? Theme.textPrimary : Theme.textDisabled
                                font.pixelSize: 14
                                font.weight: Font.DemiBold
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }

                            background: Rectangle {
                                radius: 6
                                color: parent.enabled
                                       ? (parent.pressed ? Theme.accentPressed
                                          : parent.hovered ? Theme.accentHover
                                          : Theme.accent)
                                       : Theme.buttonSecondary
                                opacity: parent.enabled ? 1.0 : 0.5
                            }
                        }
                    }
                }
            }
        }

        // ─────────────────────────────────────────────────────────
        // Step 2: Action Selection (visible after confirmation)
        // ─────────────────────────────────────────────────────────
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
                spacing: 12

                Text {
                    text: "Step 2: Choose Action"
                    color: Theme.textSecondary
                    font.pixelSize: 11
                    font.weight: Font.Medium
                }

                Row {
                    width: parent.width
                    height: parent.height - 60
                    spacing: 12

                    ActionCard {
                        id: terminalCard
                        width: (parent.width - 12) / 2
                        height: parent.height
                        title: "Terminal"
                        description: "Open a terminal with BEC environment"
                        icon: "⌘"
                        buttonText: "Open Terminal"
                    }

                    ActionCard {
                        id: guiCard
                        width: (parent.width - 12) / 2
                        height: parent.height
                        title: "GUI"
                        description: "Launch the BEC graphical interface"
                        icon: "⬚"
                        buttonText: "Launch GUI"
                    }
                }

                // Remember choice checkbox
                Rectangle {
                    width: parent.width
                    height: 28
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
                            implicitWidth: 18
                            implicitHeight: 18
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
