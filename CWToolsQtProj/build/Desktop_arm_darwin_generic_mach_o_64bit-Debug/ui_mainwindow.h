/********************************************************************************
** Form generated from reading UI file 'mainwindow.ui'
**
** Created by: Qt User Interface Compiler version 6.9.0
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_MAINWINDOW_H
#define UI_MAINWINDOW_H

#include <QtCore/QLocale>
#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QCheckBox>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QFormLayout>
#include <QtWidgets/QGridLayout>
#include <QtWidgets/QLabel>
#include <QtWidgets/QLineEdit>
#include <QtWidgets/QMainWindow>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QSlider>
#include <QtWidgets/QSpacerItem>
#include <QtWidgets/QSpinBox>
#include <QtWidgets/QStatusBar>
#include <QtWidgets/QTabWidget>
#include <QtWidgets/QVBoxLayout>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_MainWindow
{
public:
    QWidget *centralwidget;
    QVBoxLayout *verticalLayout_2;
    QLabel *label;
    QTabWidget *tabWidget;
    QWidget *tab;
    QVBoxLayout *verticalLayout;
    QPushButton *btn_buildZeroGrp;
    QPushButton *btn_placeLocatorAtVertCenter;
    QPushButton *btn_renameShapeNodes;
    QPushButton *btn_setHistoryNotInteresting;
    QPushButton *btn_sortSelection;
    QPushButton *btn_mergeCrv;
    QWidget *tab_2;
    QSpinBox *spinBox;
    QWidget *tab_ctrl;
    QWidget *wgt_colorPicker;
    QGridLayout *gridLayout;
    QPushButton *btn_setCtrlColor;
    QLabel *lbl_colorIndicator;
    QPushButton *btn_setCtrlWidth;
    QLineEdit *txt_width;
    QSlider *sdr_width;
    QLabel *lbl_color;
    QSlider *sdr_color;
    QLabel *lbl_width;
    QSpacerItem *horizontalSpacer;
    QWidget *widget_2;
    QFormLayout *formLayout;
    QLabel *lbl_ctrlName;
    QLineEdit *txt_ctrlName;
    QPushButton *btn_extractShape;
    QWidget *widget_3;
    QGridLayout *gridLayout_3;
    QCheckBox *cbx_ctrlZeroGrp;
    QPushButton *btn_createShape;
    QComboBox *cbb_setCtrlShape;
    QPushButton *btn_close;
    QStatusBar *statusbar;

    void setupUi(QMainWindow *MainWindow)
    {
        if (MainWindow->objectName().isEmpty())
            MainWindow->setObjectName("MainWindow");
        MainWindow->resize(300, 600);
        QSizePolicy sizePolicy(QSizePolicy::Policy::Preferred, QSizePolicy::Policy::Preferred);
        sizePolicy.setHorizontalStretch(0);
        sizePolicy.setVerticalStretch(0);
        sizePolicy.setHeightForWidth(MainWindow->sizePolicy().hasHeightForWidth());
        MainWindow->setSizePolicy(sizePolicy);
        MainWindow->setMinimumSize(QSize(300, 600));
        MainWindow->setMaximumSize(QSize(300, 600));
        centralwidget = new QWidget(MainWindow);
        centralwidget->setObjectName("centralwidget");
        verticalLayout_2 = new QVBoxLayout(centralwidget);
        verticalLayout_2->setObjectName("verticalLayout_2");
        label = new QLabel(centralwidget);
        label->setObjectName("label");

        verticalLayout_2->addWidget(label);

        tabWidget = new QTabWidget(centralwidget);
        tabWidget->setObjectName("tabWidget");
        tabWidget->setMinimumSize(QSize(280, 430));
        tabWidget->setMaximumSize(QSize(280, 430));
#if QT_CONFIG(tooltip)
        tabWidget->setToolTip(QString::fromUtf8(""));
#endif // QT_CONFIG(tooltip)
        tabWidget->setLocale(QLocale(QLocale::English, QLocale::Canada));
        tab = new QWidget();
        tab->setObjectName("tab");
        verticalLayout = new QVBoxLayout(tab);
        verticalLayout->setObjectName("verticalLayout");
        btn_buildZeroGrp = new QPushButton(tab);
        btn_buildZeroGrp->setObjectName("btn_buildZeroGrp");
        QSizePolicy sizePolicy1(QSizePolicy::Policy::Minimum, QSizePolicy::Policy::Preferred);
        sizePolicy1.setHorizontalStretch(0);
        sizePolicy1.setVerticalStretch(0);
        sizePolicy1.setHeightForWidth(btn_buildZeroGrp->sizePolicy().hasHeightForWidth());
        btn_buildZeroGrp->setSizePolicy(sizePolicy1);
        btn_buildZeroGrp->setLocale(QLocale(QLocale::English, QLocale::Canada));

        verticalLayout->addWidget(btn_buildZeroGrp);

        btn_placeLocatorAtVertCenter = new QPushButton(tab);
        btn_placeLocatorAtVertCenter->setObjectName("btn_placeLocatorAtVertCenter");
        sizePolicy1.setHeightForWidth(btn_placeLocatorAtVertCenter->sizePolicy().hasHeightForWidth());
        btn_placeLocatorAtVertCenter->setSizePolicy(sizePolicy1);
        btn_placeLocatorAtVertCenter->setLocale(QLocale(QLocale::English, QLocale::Canada));

        verticalLayout->addWidget(btn_placeLocatorAtVertCenter);

        btn_renameShapeNodes = new QPushButton(tab);
        btn_renameShapeNodes->setObjectName("btn_renameShapeNodes");
        sizePolicy1.setHeightForWidth(btn_renameShapeNodes->sizePolicy().hasHeightForWidth());
        btn_renameShapeNodes->setSizePolicy(sizePolicy1);
        btn_renameShapeNodes->setLocale(QLocale(QLocale::English, QLocale::Canada));

        verticalLayout->addWidget(btn_renameShapeNodes);

        btn_setHistoryNotInteresting = new QPushButton(tab);
        btn_setHistoryNotInteresting->setObjectName("btn_setHistoryNotInteresting");
        sizePolicy1.setHeightForWidth(btn_setHistoryNotInteresting->sizePolicy().hasHeightForWidth());
        btn_setHistoryNotInteresting->setSizePolicy(sizePolicy1);
        btn_setHistoryNotInteresting->setLocale(QLocale(QLocale::English, QLocale::Canada));

        verticalLayout->addWidget(btn_setHistoryNotInteresting);

        btn_sortSelection = new QPushButton(tab);
        btn_sortSelection->setObjectName("btn_sortSelection");
        sizePolicy1.setHeightForWidth(btn_sortSelection->sizePolicy().hasHeightForWidth());
        btn_sortSelection->setSizePolicy(sizePolicy1);
        btn_sortSelection->setLocale(QLocale(QLocale::English, QLocale::Canada));

        verticalLayout->addWidget(btn_sortSelection);

        btn_mergeCrv = new QPushButton(tab);
        btn_mergeCrv->setObjectName("btn_mergeCrv");
        sizePolicy1.setHeightForWidth(btn_mergeCrv->sizePolicy().hasHeightForWidth());
        btn_mergeCrv->setSizePolicy(sizePolicy1);
        btn_mergeCrv->setLocale(QLocale(QLocale::English, QLocale::Canada));

        verticalLayout->addWidget(btn_mergeCrv);

        tabWidget->addTab(tab, QString());
        tab_2 = new QWidget();
        tab_2->setObjectName("tab_2");
        spinBox = new QSpinBox(tab_2);
        spinBox->setObjectName("spinBox");
        spinBox->setGeometry(QRect(110, 200, 42, 22));
        spinBox->setWrapping(false);
        spinBox->setButtonSymbols(QAbstractSpinBox::ButtonSymbols::NoButtons);
        tabWidget->addTab(tab_2, QString());
        tab_ctrl = new QWidget();
        tab_ctrl->setObjectName("tab_ctrl");
        wgt_colorPicker = new QWidget(tab_ctrl);
        wgt_colorPicker->setObjectName("wgt_colorPicker");
        wgt_colorPicker->setGeometry(QRect(20, 91, 250, 181));
        wgt_colorPicker->setMinimumSize(QSize(250, 0));
        wgt_colorPicker->setMaximumSize(QSize(250, 16777215));
        wgt_colorPicker->setAutoFillBackground(true);
        wgt_colorPicker->setStyleSheet(QString::fromUtf8("background{rgb(0,0,0)}"));
        gridLayout = new QGridLayout(wgt_colorPicker);
        gridLayout->setObjectName("gridLayout");
        btn_setCtrlColor = new QPushButton(wgt_colorPicker);
        btn_setCtrlColor->setObjectName("btn_setCtrlColor");

        gridLayout->addWidget(btn_setCtrlColor, 3, 0, 1, 3);

        lbl_colorIndicator = new QLabel(wgt_colorPicker);
        lbl_colorIndicator->setObjectName("lbl_colorIndicator");
        lbl_colorIndicator->setEnabled(true);
        sizePolicy.setHeightForWidth(lbl_colorIndicator->sizePolicy().hasHeightForWidth());
        lbl_colorIndicator->setSizePolicy(sizePolicy);
        lbl_colorIndicator->setMinimumSize(QSize(0, 0));
        lbl_colorIndicator->setMaximumSize(QSize(500, 500));
        lbl_colorIndicator->setBaseSize(QSize(0, 0));
        lbl_colorIndicator->setLayoutDirection(Qt::LayoutDirection::LeftToRight);
        lbl_colorIndicator->setAutoFillBackground(false);
        lbl_colorIndicator->setStyleSheet(QString::fromUtf8("background-color: rgb(0, 0, 0); border: 1px solid #888;"));

        gridLayout->addWidget(lbl_colorIndicator, 2, 0, 1, 1);

        btn_setCtrlWidth = new QPushButton(wgt_colorPicker);
        btn_setCtrlWidth->setObjectName("btn_setCtrlWidth");

        gridLayout->addWidget(btn_setCtrlWidth, 7, 0, 1, 3);

        txt_width = new QLineEdit(wgt_colorPicker);
        txt_width->setObjectName("txt_width");
        txt_width->setMinimumSize(QSize(90, 0));
        txt_width->setMaximumSize(QSize(90, 16777215));
        txt_width->setInputMask(QString::fromUtf8(""));
        txt_width->setAlignment(Qt::AlignmentFlag::AlignLeading|Qt::AlignmentFlag::AlignLeft|Qt::AlignmentFlag::AlignVCenter);

        gridLayout->addWidget(txt_width, 6, 0, 1, 1);

        sdr_width = new QSlider(wgt_colorPicker);
        sdr_width->setObjectName("sdr_width");
        QSizePolicy sizePolicy2(QSizePolicy::Policy::MinimumExpanding, QSizePolicy::Policy::Fixed);
        sizePolicy2.setHorizontalStretch(0);
        sizePolicy2.setVerticalStretch(0);
        sizePolicy2.setHeightForWidth(sdr_width->sizePolicy().hasHeightForWidth());
        sdr_width->setSizePolicy(sizePolicy2);
        sdr_width->setSliderPosition(1);
        sdr_width->setOrientation(Qt::Orientation::Horizontal);

        gridLayout->addWidget(sdr_width, 6, 1, 1, 1);

        lbl_color = new QLabel(wgt_colorPicker);
        lbl_color->setObjectName("lbl_color");
        QSizePolicy sizePolicy3(QSizePolicy::Policy::Preferred, QSizePolicy::Policy::MinimumExpanding);
        sizePolicy3.setHorizontalStretch(0);
        sizePolicy3.setVerticalStretch(0);
        sizePolicy3.setHeightForWidth(lbl_color->sizePolicy().hasHeightForWidth());
        lbl_color->setSizePolicy(sizePolicy3);
        lbl_color->setMinimumSize(QSize(0, 0));
        lbl_color->setMaximumSize(QSize(16777215, 16777215));
        lbl_color->setAlignment(Qt::AlignmentFlag::AlignLeading|Qt::AlignmentFlag::AlignLeft|Qt::AlignmentFlag::AlignVCenter);
        lbl_color->setMargin(0);

        gridLayout->addWidget(lbl_color, 1, 0, 1, 1);

        sdr_color = new QSlider(wgt_colorPicker);
        sdr_color->setObjectName("sdr_color");
        sizePolicy2.setHeightForWidth(sdr_color->sizePolicy().hasHeightForWidth());
        sdr_color->setSizePolicy(sizePolicy2);
        sdr_color->setOrientation(Qt::Orientation::Horizontal);

        gridLayout->addWidget(sdr_color, 2, 1, 1, 1);

        lbl_width = new QLabel(wgt_colorPicker);
        lbl_width->setObjectName("lbl_width");
        QSizePolicy sizePolicy4(QSizePolicy::Policy::MinimumExpanding, QSizePolicy::Policy::Preferred);
        sizePolicy4.setHorizontalStretch(0);
        sizePolicy4.setVerticalStretch(0);
        sizePolicy4.setHeightForWidth(lbl_width->sizePolicy().hasHeightForWidth());
        lbl_width->setSizePolicy(sizePolicy4);
        lbl_width->setMinimumSize(QSize(0, 0));
        lbl_width->setMaximumSize(QSize(16777215, 16777215));
        lbl_width->setAlignment(Qt::AlignmentFlag::AlignLeading|Qt::AlignmentFlag::AlignLeft|Qt::AlignmentFlag::AlignVCenter);

        gridLayout->addWidget(lbl_width, 5, 0, 1, 1);

        horizontalSpacer = new QSpacerItem(40, 20, QSizePolicy::Policy::Expanding, QSizePolicy::Policy::Minimum);

        gridLayout->addItem(horizontalSpacer, 1, 1, 1, 1);

        widget_2 = new QWidget(tab_ctrl);
        widget_2->setObjectName("widget_2");
        widget_2->setGeometry(QRect(20, 12, 250, 79));
        widget_2->setMinimumSize(QSize(250, 0));
        widget_2->setMaximumSize(QSize(250, 16777215));
        formLayout = new QFormLayout(widget_2);
        formLayout->setObjectName("formLayout");
        lbl_ctrlName = new QLabel(widget_2);
        lbl_ctrlName->setObjectName("lbl_ctrlName");
        lbl_ctrlName->setMinimumSize(QSize(90, 0));
        lbl_ctrlName->setMaximumSize(QSize(90, 16777215));

        formLayout->setWidget(0, QFormLayout::ItemRole::LabelRole, lbl_ctrlName);

        txt_ctrlName = new QLineEdit(widget_2);
        txt_ctrlName->setObjectName("txt_ctrlName");

        formLayout->setWidget(0, QFormLayout::ItemRole::FieldRole, txt_ctrlName);

        btn_extractShape = new QPushButton(widget_2);
        btn_extractShape->setObjectName("btn_extractShape");

        formLayout->setWidget(1, QFormLayout::ItemRole::SpanningRole, btn_extractShape);

        widget_3 = new QWidget(tab_ctrl);
        widget_3->setObjectName("widget_3");
        widget_3->setGeometry(QRect(20, 282, 250, 84));
        widget_3->setMinimumSize(QSize(250, 0));
        widget_3->setMaximumSize(QSize(250, 16777215));
        gridLayout_3 = new QGridLayout(widget_3);
        gridLayout_3->setObjectName("gridLayout_3");
        cbx_ctrlZeroGrp = new QCheckBox(widget_3);
        cbx_ctrlZeroGrp->setObjectName("cbx_ctrlZeroGrp");

        gridLayout_3->addWidget(cbx_ctrlZeroGrp, 0, 1, 1, 1);

        btn_createShape = new QPushButton(widget_3);
        btn_createShape->setObjectName("btn_createShape");

        gridLayout_3->addWidget(btn_createShape, 1, 0, 1, 2);

        cbb_setCtrlShape = new QComboBox(widget_3);
        cbb_setCtrlShape->setObjectName("cbb_setCtrlShape");

        gridLayout_3->addWidget(cbb_setCtrlShape, 0, 0, 1, 1);

        tabWidget->addTab(tab_ctrl, QString());

        verticalLayout_2->addWidget(tabWidget);

        btn_close = new QPushButton(centralwidget);
        btn_close->setObjectName("btn_close");
        btn_close->setMinimumSize(QSize(280, 50));
        btn_close->setLocale(QLocale(QLocale::English, QLocale::Canada));

        verticalLayout_2->addWidget(btn_close);

        MainWindow->setCentralWidget(centralwidget);
        statusbar = new QStatusBar(MainWindow);
        statusbar->setObjectName("statusbar");
        MainWindow->setStatusBar(statusbar);

        retranslateUi(MainWindow);
        QObject::connect(sdr_width, &QSlider::sliderMoved, txt_width, qOverload<>(&QLineEdit::update));
        QObject::connect(txt_width, &QLineEdit::editingFinished, sdr_width, qOverload<>(&QSlider::update));

        tabWidget->setCurrentIndex(1);


        QMetaObject::connectSlotsByName(MainWindow);
    } // setupUi

    void retranslateUi(QMainWindow *MainWindow)
    {
        MainWindow->setWindowTitle(QCoreApplication::translate("MainWindow", "MainWindow", nullptr));
        label->setText(QCoreApplication::translate("MainWindow", "<html><head/><body><p align=\"center\"><span style=\" font-size:36pt;\">CW Tools</span></p></body></html>", nullptr));
        btn_buildZeroGrp->setText(QCoreApplication::translate("MainWindow", "Build zero group", nullptr));
        btn_placeLocatorAtVertCenter->setText(QCoreApplication::translate("MainWindow", "Vertices centered locator", nullptr));
        btn_renameShapeNodes->setText(QCoreApplication::translate("MainWindow", "Rename shape nodes", nullptr));
        btn_setHistoryNotInteresting->setText(QCoreApplication::translate("MainWindow", "Set history not interesting", nullptr));
        btn_sortSelection->setText(QCoreApplication::translate("MainWindow", "Sort selection in outliner", nullptr));
        btn_mergeCrv->setText(QCoreApplication::translate("MainWindow", "Merge curves", nullptr));
        tabWidget->setTabText(tabWidget->indexOf(tab), QCoreApplication::translate("MainWindow", "Utility", nullptr));
        tabWidget->setTabText(tabWidget->indexOf(tab_2), QCoreApplication::translate("MainWindow", "Rigging", nullptr));
        btn_setCtrlColor->setText(QCoreApplication::translate("MainWindow", "Set color", nullptr));
        lbl_colorIndicator->setText(QString());
        btn_setCtrlWidth->setText(QCoreApplication::translate("MainWindow", "Set width", nullptr));
        txt_width->setText(QCoreApplication::translate("MainWindow", "1.0", nullptr));
        lbl_color->setText(QCoreApplication::translate("MainWindow", "Color", nullptr));
        lbl_width->setText(QCoreApplication::translate("MainWindow", "Width", nullptr));
        lbl_ctrlName->setText(QCoreApplication::translate("MainWindow", "Control name", nullptr));
        btn_extractShape->setText(QCoreApplication::translate("MainWindow", "Add curve to library", nullptr));
        cbx_ctrlZeroGrp->setText(QCoreApplication::translate("MainWindow", "add zero grp", nullptr));
        btn_createShape->setText(QCoreApplication::translate("MainWindow", "Create ctrl shape", nullptr));
        tabWidget->setTabText(tabWidget->indexOf(tab_ctrl), QCoreApplication::translate("MainWindow", "Control", nullptr));
        btn_close->setText(QCoreApplication::translate("MainWindow", "close", nullptr));
    } // retranslateUi

};

namespace Ui {
    class MainWindow: public Ui_MainWindow {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_MAINWINDOW_H
