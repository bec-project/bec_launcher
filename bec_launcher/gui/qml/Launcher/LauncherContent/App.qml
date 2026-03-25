import QtQuick
import QtQuick.Window
import Launcher

Window {
    id: window
    readonly property int targetHeight: Math.max(
        Constants.windowMinHeight,
        Math.ceil(appForm.implicitHeight)
    )

    width: Constants.windowWidth
    height: targetHeight
    minimumWidth: Constants.windowWidth
    minimumHeight: targetHeight
    maximumWidth: Constants.windowWidth
    maximumHeight: targetHeight
    visible: true
    title: "BEC Launcher"
    color: Theme.background

    AppForm {
        id: appForm
        anchors.fill: parent
        deploymentNames: backend.deploymentNames
        deploymentPaths: backend.deploymentPaths
        selectedIndex: backend.selectedIndex
        deploymentConfirmed: backend.deploymentConfirmed
        defaultDeployment: backend.defaultDeployment
        defaultAction: backend.defaultAction
        onDeploymentSelected: (index) => backend.selectDeployment(index)
        onConfirmDeployment: backend.confirmDeployment()
        onChangeDeployment: backend.changeDeployment()
        onLaunchTerminal: backend.launchTerminal()
        onLaunchDock: backend.launchDock()
        onLaunchApp: backend.launchApp()
    }

    Connections {
        target: appForm.changeButton
        function onClicked() { appForm.changeDeployment() }
    }

    Connections {
        target: appForm.confirmButton
        function onClicked() { appForm.confirmDeployment() }
    }

    Connections {
        target: appForm.terminalCard.launchButton
        function onClicked() { appForm.launchTerminal() }
    }

    Connections {
        target: appForm.terminalCard.cardMouseArea

        function onClicked() {
            appForm.launchTerminal()
        }
        function onEntered() { appForm.terminalCard.isHovered = true }
        function onExited() { appForm.terminalCard.isHovered = false }
    }

    Connections {
        target: appForm.terminalCard.defaultToggleMouseArea

        function onClicked() {
            backend.setDefaultAction("terminal", !appForm.terminalCard.isDefault)
        }
    }

    Connections {
        target: appForm.dockCard.launchButton
        function onClicked() { appForm.launchDock() }
    }

    Connections {
        target: appForm.dockCard.cardMouseArea

        function onClicked() {
            appForm.launchDock()
        }
        function onEntered() { appForm.dockCard.isHovered = true }
        function onExited() { appForm.dockCard.isHovered = false }
    }

    Connections {
        target: appForm.dockCard.defaultToggleMouseArea

        function onClicked() {
            backend.setDefaultAction("dock", !appForm.dockCard.isDefault)
        }
    }

    Connections {
        target: appForm.appCard.launchButton
        function onClicked() { appForm.launchApp() }
    }

    Connections {
        target: appForm.appCard.cardMouseArea

        function onClicked() {
            appForm.launchApp()
        }
        function onEntered() { appForm.appCard.isHovered = true }
        function onExited() { appForm.appCard.isHovered = false }
    }

    Connections {
        target: appForm.appCard.defaultToggleMouseArea

        function onClicked() {
            backend.setDefaultAction("app", !appForm.appCard.isDefault)
        }
    }

    Connections {
        target: appForm.deploymentRepeater

        function onItemAdded(index, item) {
            item.cardMouseArea.clicked.connect(function() {
                appForm.deploymentSelected(index)
            })
            item.defaultToggleMouseArea.clicked.connect(function () {
                backend.setDefaultDeployment(index, !item.isDefault)
            })
            item.cardMouseArea.entered.connect(function() {
                item.isHovered = true
            })
            item.cardMouseArea.exited.connect(function() {
                item.isHovered = false
            })
        }
    }

    Connections {
        target: backend

        function onQuitApplication() {
            console.log("Quitting application")
            Qt.quit()
        }
    }
}
