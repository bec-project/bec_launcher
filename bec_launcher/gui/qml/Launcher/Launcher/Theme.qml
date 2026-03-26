pragma Singleton
import QtQuick

QtObject {
    readonly property color background: "#0e1017"
    readonly property color backgroundCard: "#161921"
    readonly property color backgroundCardHover: "#1c2029"
    readonly property color backgroundCardSelected: "#1f2533"
    readonly property color backgroundCardDefault: "#172435"
    readonly property color backgroundCardSelectedDefault: "#203247"
    readonly property color backgroundInput: "#0d1015"

    readonly property color border: "#2b3342"
    readonly property color borderHover: "#3a4556"
    readonly property color borderDefault: "#52b8eb"
    readonly property color borderSelected: "#3daee9"

    readonly property color textPrimary: "#ffffff"
    readonly property color textSecondary: "#b8c0cc"
    readonly property color textMuted: "#6b7280"
    readonly property color textDisabled: "#4b5563"

    readonly property color accent: "#3daee9"
    readonly property color accentHover: "#52b8eb"
    readonly property color accentPressed: "#2a9cd8"

    readonly property color badgeProd: "#22c55e"
    readonly property color badgeProdBg: Qt.rgba(34/255, 197/255, 94/255, 0.15)
    readonly property color badgeTest: "#f59e0b"
    readonly property color badgeTestBg: Qt.rgba(245/255, 158/255, 11/255, 0.15)
    readonly property color badgeDev: "#3b82f6"
    readonly property color badgeDevBg: Qt.rgba(59/255, 130/255, 246/255, 0.15)

    readonly property color buttonSecondary: "#1f2937"
    readonly property color buttonSecondaryHover: "#374151"

    readonly property color divider: "#2b3342"

    readonly property color tooltipBackground: "#111924"
    readonly property color tooltipBorder: "#3a4556"
    readonly property color tooltipText: "#e8edf5"
    readonly property color tooltipTextMuted: "#b8c0cc"

    readonly property int radiusSmall: 6
    readonly property int radiusMedium: 10
}
