/*
  App.qml - Main application entry point
  Connects AppForm.ui.qml to the backend and wires up signal handlers
*/
import QtQuick
import QtQuick.Window
import Launcher

Window {
    id: window
    width: Constants.width
    height: Constants.height
    minimumWidth: Constants.width
    minimumHeight: Constants.height
    maximumWidth: Constants.width
    maximumHeight: Constants.height
    visible: true
    title: "BEC Launcher"
    color: Theme.background

    AppForm {
        id: appForm
        anchors.fill: parent

        // Connect to backend data
        deploymentNames: backend.deploymentNames
        deploymentPaths: backend.deploymentPaths
        selectedIndex: backend.selectedIndex
        deploymentConfirmed: backend.deploymentConfirmed
        appVersion: backend.version
        rememberChoice: backend.rememberChoice

        // Connect signals to backend slots
        onDeploymentSelected: (index) => backend.selectDeployment(index)
        onConfirmDeployment: backend.confirmDeployment()
        onChangeDeployment: backend.changeDeployment()
        onLaunchTerminal: backend.launchTerminal()
        onLaunchGui: backend.launchGui()
        onRememberChoiceToggled: (checked) => backend.setRememberChoice(checked)
    }

    // Wire up button click handlers
    Connections {
        target: appForm.changeButton
        function onClicked() { appForm.changeDeployment() }
    }

    Connections {
        target: appForm.confirmButton
        function onClicked() { appForm.confirmDeployment() }
    }

    // Wire up action card handlers
    Connections {
        target: appForm.terminalCard.launchButton
        function onClicked() { appForm.launchTerminal() }
    }

    Connections {
        target: appForm.terminalCard.cardMouseArea
        function onEntered() { appForm.terminalCard.isHovered = true }
        function onExited() { appForm.terminalCard.isHovered = false }
    }

    Connections {
        target: appForm.guiCard.launchButton
        function onClicked() { appForm.launchGui() }
    }

    Connections {
        target: appForm.guiCard.cardMouseArea
        function onEntered() { appForm.guiCard.isHovered = true }
        function onExited() { appForm.guiCard.isHovered = false }
    }

    // Connect deployment card clicks via Repeater itemAdded
    Connections {
        target: appForm.deploymentRepeater

        function onItemAdded(index, item) {
            // Connect click handler
            item.cardMouseArea.clicked.connect(function() {
                appForm.deploymentSelected(index)
            })
            // Connect hover handlers
            item.cardMouseArea.entered.connect(function() {
                item.isHovered = true
            })
            item.cardMouseArea.exited.connect(function() {
                item.isHovered = false
            })
        }
    }

    // Connect remember checkbox
    Connections {
        target: appForm.rememberCheckbox
        function onCheckedChanged() {
            appForm.rememberChoiceToggled(appForm.rememberCheckbox.checked)
        }
    }

    // Handle signals from backend
    Connections {
        target: backend

        function onAutoLaunchTriggered(action) {
            console.log("Auto-launching:", action)
            if (action === "terminal") {
                appForm.launchTerminal()
            } else if (action === "gui") {
                appForm.launchGui()
            }
        }

        function onQuitApplication() {
            console.log("Quitting application")
            Qt.quit()
        }
    }
}
