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
        enabled: !backend.launchInProgress && !backend.launchHasError
        opacity: backend.launchInProgress || backend.launchHasError ? 0.0 : 1.0
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

    // Slim background cache warm-up indicator pinned to the window bottom.
    Rectangle {
        id: warmupBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 22
        // Declared between AppForm and LaunchBanner: overlays the form's bottom
        // padding, while a launch banner still covers it.
        color: Qt.rgba(8 / 255, 10 / 255, 18 / 255, 0.92)
        visible: opacity > 0
        opacity: backend.cacheWarmupActive || lingerTimer.running ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 350 } }

        property bool wasActive: false
        Timer { id: lingerTimer; interval: 4000 }
        Connections {
            target: backend
            function onCacheWarmupChanged() {
                if (warmupBar.wasActive && !backend.cacheWarmupActive
                        && backend.cacheWarmupText !== "")
                    lingerTimer.restart()
                warmupBar.wasActive = backend.cacheWarmupActive
            }
        }

        Rectangle {
            anchors.top: parent.top
            width: parent.width
            height: 1
            color: Qt.rgba(1, 1, 1, 0.06)
        }

        Row {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: 12
            spacing: 8

            Rectangle {
                width: 7; height: 7; radius: 3.5
                anchors.verticalCenter: parent.verticalCenter
                color: backend.cacheWarmupActive ? Theme.accent : Theme.badgeProd
                SequentialAnimation on opacity {
                    running: backend.cacheWarmupActive && warmupBar.visible
                    loops: Animation.Infinite
                    NumberAnimation { from: 1.0; to: 0.3; duration: 600 }
                    NumberAnimation { from: 0.3; to: 1.0; duration: 600 }
                }
            }

            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: backend.cacheWarmupText
                color: Theme.textMuted
                font.pixelSize: 11
            }
        }
    }

    LaunchBanner {
        id: launchBanner
        anchors.fill: parent
        visible: backend.launchInProgress || backend.launchHasError
        deploymentName: backend.launchDeployment
        launchMode: backend.launchMode
        statusText: backend.launchStatus
        elapsedSeconds: backend.launchElapsedSeconds
        hasError: backend.launchHasError
        stages: backend.launchStages
        stageCount: backend.launchStageCount
        expectedStages: backend.launchExpectedStages
        currentStage: backend.launchCurrentStage
        isStalled: backend.launchIsStalled
        coldStart: backend.launchIsColdStart
        onDismissRequested: backend.dismissLaunchError()
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
