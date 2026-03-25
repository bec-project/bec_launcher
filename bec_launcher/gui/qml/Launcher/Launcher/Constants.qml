pragma Singleton
import QtQuick

QtObject {
    readonly property int windowWidth: 800
    readonly property int windowMinHeight: 320

    readonly property int pageMargin: 16
    readonly property int sectionPadding: 12
    readonly property int sectionGap: 12
    readonly property int sectionRadius: 14
    readonly property int headerHeight: 30
    readonly property int sectionHeaderHeight: 25
    readonly property int stepLabelHeight: 20
    readonly property int dividerThickness: 1

    readonly property int deploymentListVisibleCount: 4
    readonly property int deploymentCardPadding: 12
    readonly property int deploymentCardGap: 8
    readonly property int defaultToggleHeight: 22

    readonly property int changeButtonWidth: 80
    readonly property int smallButtonHeight: 32
    readonly property int primaryButtonHeight: 40

    readonly property int actionCardHeight: 170
    readonly property int actionCardGap: 12
    readonly property int actionCardPadding: 12
    readonly property int actionCardButtonGap: 6
    readonly property int actionCardIconSize: 64
    readonly property int actionCardTitleHeight: 20
    readonly property int actionCardButtonHeight: 40
}
