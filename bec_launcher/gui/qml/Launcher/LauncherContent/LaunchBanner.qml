import QtQuick
import QtQuick.Layouts
import Launcher

Rectangle {
    id: root

    // --- Bindings from the backend (see App.qml) --------------------------
    property string deploymentName: ""
    property string launchMode: ""
    property string statusText: "Starting GUI..."
    property int elapsedSeconds: 0
    property bool hasError: false
    property var stages: []
    property int stageCount: 0
    property int expectedStages: 9
    property string currentStage: ""
    property bool isStalled: false
    property bool coldStart: false

    signal dismissRequested()

    readonly property bool isAppLaunch: root.launchMode.toLowerCase().indexOf("app") >= 0
    readonly property url modeIcon: root.isAppLaunch ? "images/BEC_app.png" : "images/BEC_comp.png"
    readonly property bool busy: !root.hasError
    // Gate the infinite animations on visibility so an idle launcher doesn't spin them.
    readonly property bool active: root.visible && !root.hasError
    // The child streams a stage only once it finishes, so we never show a full bar
    // until the GUI actually reports ready (at which point the banner is dismissed).
    readonly property real progress: root.expectedStages > 0
        ? Math.min(root.stageCount / root.expectedStages, 0.97)
        : 0.0
    property real pointerX: width / 2
    property real pointerY: height / 2

    // Shared ellipsis ticker ("", ".", "..", "...") for title + working row.
    property int dotPhase: 0
    readonly property string dotsText: ".".repeat(root.dotPhase)
    Timer {
        interval: 400
        running: root.active
        repeat: true
        onTriggered: root.dotPhase = (root.dotPhase + 1) % 4
    }

    clip: true
    color: "#080a12"

    // ----- Ambient background --------------------------------------------
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Vertical
            GradientStop { position: 0.0; color: "#070912" }
            GradientStop {
                id: animatedStop
                position: 0.52
                color: root.hasError ? "#2a1418" : "#10202d"
            }
            GradientStop { position: 1.0; color: "#12151f" }
        }
    }

    Rectangle {
        width: parent.width * 1.35
        height: 120
        x: -parent.width * 0.18 + ((root.pointerX / Math.max(root.width, 1)) - 0.5) * 52
        y: 40 + ((root.pointerY / Math.max(root.height, 1)) - 0.5) * 30
        rotation: -11
        opacity: root.hasError ? 0.22 : 0.38
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.00; color: "#003daee9" }
            GradientStop { position: 0.34; color: "#303daee9" }
            GradientStop { position: 0.68; color: "#1822c55e" }
            GradientStop { position: 1.00; color: "#003daee9" }
        }
    }

    Rectangle {
        width: parent.width * 1.25
        height: 150
        x: -parent.width * 0.12 - ((root.pointerX / Math.max(root.width, 1)) - 0.5) * 40
        y: parent.height - 155 - ((root.pointerY / Math.max(root.height, 1)) - 0.5) * 25
        rotation: 8
        opacity: root.hasError ? 0.18 : 0.28
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.00; color: "#0052b8eb" }
            GradientStop { position: 0.42; color: "#234f46e5" }
            GradientStop { position: 0.76; color: "#143daee9" }
            GradientStop { position: 1.00; color: "#0052b8eb" }
        }
    }

    SequentialAnimation {
        running: root.active
        loops: Animation.Infinite
        ColorAnimation {
            target: animatedStop; property: "color"
            to: "#122b30"; duration: 2600; easing.type: Easing.InOutSine
        }
        ColorAnimation {
            target: animatedStop; property: "color"
            to: "#101b2e"; duration: 2600; easing.type: Easing.InOutSine
        }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
        onPositionChanged: (mouse) => { root.pointerX = mouse.x; root.pointerY = mouse.y }
        onExited: { root.pointerX = root.width / 2; root.pointerY = root.height / 2 }
    }

    // ----- Foreground panel ----------------------------------------------
    Rectangle {
        id: panel
        width: Math.min(parent.width - 48, 600)
        height: Math.min(parent.height - 24, 430)
        anchors.centerIn: parent
        radius: Theme.radiusMedium
        color: Qt.rgba(22 / 255, 25 / 255, 33 / 255, 0.90)

        // Breathing accent border while busy; solid state colors otherwise.
        property real borderGlow: 0.0
        border.width: 1
        border.color: root.hasError
            ? "#ef4444"
            : (root.isStalled
                ? "#f59e0b"
                : Qt.rgba(82 / 255, 184 / 255, 235 / 255, 0.28 + 0.32 * panel.borderGlow))

        SequentialAnimation {
            running: root.active && !root.isStalled
            loops: Animation.Infinite
            NumberAnimation {
                target: panel; property: "borderGlow"
                from: 0.0; to: 1.0; duration: 1700; easing.type: Easing.InOutSine
            }
            NumberAnimation {
                target: panel; property: "borderGlow"
                from: 1.0; to: 0.0; duration: 1700; easing.type: Easing.InOutSine
            }
        }

        // Entrance: gently scale/fade in whenever the banner becomes visible.
        scale: root.visible ? 1.0 : 0.96
        opacity: root.visible ? 1.0 : 0.0
        Behavior on scale { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
        Behavior on opacity { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }

        Rectangle {
            anchors.fill: parent
            anchors.margins: 1
            radius: Theme.radiusMedium - 1
            color: "transparent"
            border.width: 1
            border.color: Qt.rgba(1, 1, 1, 0.04)
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 22
            spacing: 12

            // --- Header -------------------------------------------------
            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                Item {
                    Layout.preferredWidth: 60
                    Layout.preferredHeight: 60
                    Image {
                        anchors.fill: parent
                        source: root.modeIcon
                        fillMode: Image.PreserveAspectFit
                        smooth: true
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Text {
                        Layout.fillWidth: true
                        text: root.hasError
                            ? "Launch failed"
                            : (root.isStalled
                                ? "Still launching BEC" + root.dotsText
                                : "Launching BEC" + root.dotsText)
                        color: root.hasError ? "#fca5a5" : Theme.textPrimary
                        font.pixelSize: 22
                        font.bold: true
                        elide: Text.ElideRight
                    }
                    Text {
                        Layout.fillWidth: true
                        text: root.launchMode + (root.deploymentName ? "  •  " + root.deploymentName : "")
                        color: Theme.textSecondary
                        font.pixelSize: 14
                        elide: Text.ElideRight
                    }
                }

                Text {
                    text: root.elapsedSeconds + "s"
                    color: Theme.textMuted
                    font.pixelSize: 15
                    font.bold: true
                }
            }

            // --- Progress meter (determinate fill + shimmer + comet head) ---
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 6
                visible: !root.hasError

                Rectangle {
                    id: track
                    anchors.fill: parent
                    radius: height / 2
                    color: Qt.rgba(1, 1, 1, 0.07)
                    clip: true

                    Rectangle {
                        id: fill
                        height: parent.height
                        radius: height / 2
                        width: parent.width * root.progress
                        color: root.isStalled ? Theme.badgeTest : Theme.accent
                        Behavior on width { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }
                    }

                    // Shimmer sweep — constant motion so the user always sees life.
                    Rectangle {
                        height: parent.height
                        width: parent.width * 0.35
                        opacity: root.busy ? 0.9 : 0.0
                        gradient: Gradient {
                            orientation: Gradient.Horizontal
                            GradientStop { position: 0.0; color: "#00ffffff" }
                            GradientStop { position: 0.5; color: Qt.rgba(1, 1, 1, 0.28) }
                            GradientStop { position: 1.0; color: "#00ffffff" }
                        }
                        XAnimator on x {
                            // Wait for a real track width so from/to don't latch to 0.
                            running: root.active && track.width > 0
                            loops: Animation.Infinite
                            from: -track.width * 0.35
                            to: track.width
                            duration: 1300
                        }
                    }
                }

                // Pulsing comet head riding the fill edge.
                Rectangle {
                    id: comet
                    width: 10; height: 10; radius: 5
                    anchors.verticalCenter: track.verticalCenter
                    x: Math.max(fill.width - 5, 0)
                    visible: root.busy && root.progress > 0
                    color: root.isStalled ? Theme.badgeTest : Theme.accentHover
                    Rectangle {
                        anchors.centerIn: parent
                        width: 4; height: 4; radius: 2
                        color: "#ffffff"
                    }
                    SequentialAnimation on scale {
                        running: root.active && root.progress > 0
                        loops: Animation.Infinite
                        NumberAnimation { from: 1.0; to: 1.45; duration: 650; easing.type: Easing.InOutSine }
                        NumberAnimation { from: 1.45; to: 1.0; duration: 650; easing.type: Easing.InOutSine }
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                visible: !root.hasError
                text: "Step " + root.stageCount + " of ~" + root.expectedStages
                color: Theme.textMuted
                font.pixelSize: 12
            }

            // --- First-launch (cold start) hint chip --------------------
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: coldRow.implicitHeight + 12
                radius: Theme.radiusSmall
                color: Qt.rgba(245 / 255, 158 / 255, 11 / 255, 0.10)
                border.width: 1
                border.color: Qt.rgba(245 / 255, 158 / 255, 11 / 255, 0.35)
                visible: opacity > 0
                opacity: root.coldStart && !root.hasError ? 1.0 : 0.0
                Behavior on opacity { NumberAnimation { duration: 300 } }

                RowLayout {
                    id: coldRow
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    spacing: 8

                    Rectangle {
                        Layout.preferredWidth: 8
                        Layout.preferredHeight: 8
                        radius: 4
                        color: Theme.badgeTest
                        SequentialAnimation on opacity {
                            running: root.active && root.coldStart
                            loops: Animation.Infinite
                            NumberAnimation { from: 1.0; to: 0.35; duration: 700 }
                            NumberAnimation { from: 0.35; to: 1.0; duration: 700 }
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "First launch detected — Python is building its bytecode caches. "
                            + "This start takes longer; the next ones will be much faster."
                        color: Theme.textSecondary
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                    }
                }
            }

            // --- Streaming stage checklist ------------------------------
            ListView {
                id: stageList
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                model: root.stages
                spacing: 4
                boundsBehavior: Flickable.StopAtBounds
                onCountChanged: positionViewAtEnd()

                delegate: RowLayout {
                    id: stageRow
                    width: ListView.view.width
                    spacing: 10

                    Rectangle {
                        id: checkBadge
                        Layout.preferredWidth: 18
                        Layout.preferredHeight: 18
                        radius: 9
                        color: Qt.rgba(34 / 255, 197 / 255, 94 / 255, 0.16)
                        Text {
                            anchors.centerIn: parent
                            text: "✓"
                            color: Theme.badgeProd
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: modelData.name
                        color: Theme.textSecondary
                        font.pixelSize: 13
                        elide: Text.ElideRight
                    }

                    Text {
                        text: modelData.ms + " ms"
                        color: modelData.ms > 3000 ? Theme.badgeTest : Theme.textMuted
                        font.pixelSize: 12
                    }

                    // Slide + fade each freshly streamed row in; pop the checkmark.
                    opacity: 0
                    x: -16
                    Component.onCompleted: rowIn.start()
                    ParallelAnimation {
                        id: rowIn
                        NumberAnimation {
                            target: stageRow; property: "opacity"
                            from: 0; to: 1; duration: 280; easing.type: Easing.OutCubic
                        }
                        NumberAnimation {
                            target: stageRow; property: "x"
                            from: -16; to: 0; duration: 280; easing.type: Easing.OutCubic
                        }
                        NumberAnimation {
                            target: checkBadge; property: "scale"
                            from: 0.4; to: 1.0; duration: 340; easing.type: Easing.OutBack
                        }
                    }
                }

                // Active "working" row pinned after the last finished stage.
                footer: RowLayout {
                    width: stageList.width
                    height: root.busy ? 26 : 0
                    visible: root.busy
                    spacing: 10

                    Item {
                        Layout.preferredWidth: 18
                        Layout.preferredHeight: 18
                        Rectangle {
                            anchors.fill: parent
                            radius: 9
                            color: "transparent"
                            border.width: 2
                            border.color: Qt.rgba(82 / 255, 184 / 255, 235 / 255, 0.20)
                        }
                        Rectangle {
                            anchors.fill: parent
                            radius: 9
                            color: "transparent"
                            border.width: 2
                            border.color: root.isStalled ? Theme.badgeTest : Theme.accent
                            Rectangle {
                                width: 9; height: 10
                                anchors.left: parent.left
                                anchors.bottom: parent.bottom
                                color: panel.color
                            }
                            RotationAnimation on rotation {
                                running: root.active
                                loops: Animation.Infinite
                                from: 0; to: 360; duration: 1200
                            }
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: root.isStalled
                            ? root.statusText
                            : (root.stageCount === 0 ? root.statusText : "Working") + root.dotsText
                        color: root.isStalled ? Theme.badgeTest : Theme.textPrimary
                        font.pixelSize: 13
                        elide: Text.ElideRight
                    }
                }
            }

            // --- Error / stall recovery --------------------------------
            RowLayout {
                Layout.fillWidth: true
                visible: root.hasError || root.isStalled
                spacing: 12

                Text {
                    Layout.fillWidth: true
                    text: root.hasError
                        ? root.statusText
                        : "Taking longer than usual — you can keep waiting or go back."
                    color: root.hasError ? "#fca5a5" : Theme.textSecondary
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                }

                Rectangle {
                    Layout.preferredWidth: 150
                    Layout.preferredHeight: 34
                    radius: Theme.radiusSmall
                    color: backMouse.containsMouse ? Theme.buttonSecondaryHover : Theme.buttonSecondary
                    border.width: 1
                    border.color: Theme.border
                    Text {
                        anchors.centerIn: parent
                        text: "Back to launcher"
                        color: Theme.textPrimary
                        font.pixelSize: 13
                    }
                    MouseArea {
                        id: backMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.dismissRequested()
                    }
                }
            }
        }
    }
}
