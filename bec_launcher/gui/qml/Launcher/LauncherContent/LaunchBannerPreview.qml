import QtQuick
import QtQuick.Window
import Launcher

Window {
    width: Constants.windowWidth
    height: 460
    visible: true
    title: "BEC Launcher Banner Preview"
    color: Theme.background

    LaunchBanner {
        anchors.fill: parent
        deploymentName: demoState.deploymentName
        launchMode: demoState.launchMode
        statusText: demoState.statusText
        elapsedSeconds: demoState.elapsedSeconds
        hasError: demoState.hasError
        stages: demoState.stages
        stageCount: demoState.stageCount
        expectedStages: demoState.expectedStages
        currentStage: demoState.currentStage
        isStalled: demoState.isStalled
        coldStart: demoState.coldStart
    }
}
