/* Locate32 - Copyright (c) 1997-2010 Janne Huttunen */
/* Dazzle-Locate64 modifications - Copyright (c) 2026 Dustin Darcy */

#include <HFCLib.h>
#include "Locate32.h"

#include <Winternl.h>

// RtlGetVersion returns the true OS version (GetVersionEx lies after Win8.1)
typedef NTSTATUS (WINAPI *RtlGetVersionPtr)(PRTL_OSVERSIONINFOW);

static BOOL GetTrueWindowsVersion(RTL_OSVERSIONINFOW* osvi)
{
	HMODULE hNtdll = GetModuleHandleW(L"ntdll.dll");
	if (hNtdll == NULL) return FALSE;
	RtlGetVersionPtr pRtlGetVersion = (RtlGetVersionPtr)GetProcAddress(hNtdll, "RtlGetVersion");
	if (pRtlGetVersion == NULL) return FALSE;
	osvi->dwOSVersionInfoSize = sizeof(RTL_OSVERSIONINFOW);
	return pRtlGetVersion(osvi) == 0; // STATUS_SUCCESS
}

BOOL CAboutDlg::OnCommand(WORD wID, WORD wNotifyCode, HWND hControl)
{
	switch(wID)
	{
	case IDCANCEL:
	case IDC_OK:
		{
			EndDialog(0);
			break;
		}
	case IDC_MAILME:
		{
			// Original locate32.net contact page is dead; redirect to the
			// Dazzle-Locate64 GitHub Issues page for bug reports / feedback.
			CWaitCursor wait;
			ShellFunctions::ShellExecute(*this,NULL,"https://github.com/DazzleTools/Dazzle-Locate64/issues",
				NULL,NULL,0);
			break;
		}
	case IDC_GOTOHOMEPAGE:
		{
			// Original locate32.net is dead; point the homepage button at
			// the Dazzle-Locate64 repository.
			CWaitCursor wait;
			ShellFunctions::ShellExecute(*this,NULL,"https://github.com/DazzleTools/Dazzle-Locate64",
				NULL,NULL,0);
			break;
		}
	case IDC_YOURRIGHT:
		{
			// Dazzle-Locate64: the "[donations]" link in the freeware text
			// now points at the Dazzle-Locate64 maintainer's tip jar.
			// (The PayPal donate-button graphic below still goes to the
			// original locate32.net author's PayPal as a tribute.)
			CWaitCursor wait;
			ShellFunctions::ShellExecute(*this,NULL,
				"https://buymeacoffee.com/djdarcy",
				NULL,NULL,0);
			break;
		}
	case IDC_DONATE:
		{
			// Original PayPal donate link kept as a tribute to the
			// upstream Locate32 author (Janne Huttunen).
			CWaitCursor wait;
			ShellFunctions::ShellExecute(*this,NULL,
				"https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=Janne%2eHuttunen%40locate32%2enet&lc=FI&item_name=Locate32&no_shipping=1&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donate_LG%2egif%3aNonHosted",
				NULL,NULL,0);
			break;
		}
	}
	return FALSE;
}

BOOL CAboutDlg::OnClose()
{
	CDialog::OnClose();
	EndDialog(0);
	return FALSE;
}

BOOL CAboutDlg::OnInitDialog(HWND hwndFocus)
{
	CDialog::OnInitDialog(hwndFocus);
	CWaitCursor wait;
	OSVERSIONINFO ver; // Used in fallback path
	CStringW text,text2;

	// Setting banner and donate button
	SendDlgItemMessage(IDC_ABOUTBANNER,STM_SETIMAGE,IMAGE_BITMAP,
		(LPARAM)LoadImage(IDB_ABOUTBANNER,IMAGE_BITMAP,0,0,LR_SHARED|LR_DEFAULTSIZE));
	SendDlgItemMessage(IDC_DONATE,STM_SETIMAGE,IMAGE_BITMAP,
		(LPARAM)LoadImage(IDB_DONATE,IMAGE_BITMAP,0,0,LR_SHARED|LR_DEFAULTSIZE));
	
	// Creating copyright and version strings
	{
		CStringW str;
#ifdef _DEBUG
		str.Format(L"%s (c) 1997-2010 Janne Huttunen\nDazzle-Locate64 (c) 2026 Dustin Darcy\nTHIS IS DEBUG VERSION, %s %s",
			(LPCWSTR)ID2W(IDS_COPYRIGHT),(LPCWSTR)A2W(__DATE__),(LPCWSTR)A2W(__TIME__));
#else
		str.Format(L"%s (c) 1997-2010 Janne Huttunen\nDazzle-Locate64 (c) 2026 Dustin Darcy",(LPCWSTR)ID2W(IDS_COPYRIGHT));
#endif
		SetDlgItemText(IDC_COPYRIGHT,str);

		if (IsUnicodeSystem())
		{
			CStringW sExeName=GetApp()->GetExeNameW();
			UINT iDataLength=GetFileVersionInfoSizeW(sExeName,NULL);
			BYTE* pData=new BYTE[iDataLength];
			GetFileVersionInfoW(sExeName,NULL,iDataLength,pData);
			VOID* pTranslations,* pProductVersion=NULL;
			VerQueryValueW(pData,L"VarFileInfo\\Translation",&pTranslations,&iDataLength);
			WCHAR szTranslation[100];
			StringCbPrintfW(szTranslation,100*sizeof(WCHAR),L"\\StringFileInfo\\%04X%04X\\ProductVersion",LPWORD(pTranslations)[0],LPWORD(pTranslations)[1]);
			if (!VerQueryValueW(pData,szTranslation,&pProductVersion,&iDataLength))
				VerQueryValueW(pData,L"\\StringFileInfo\\040904b0\\ProductVersion",&pProductVersion,&iDataLength);
			
			if (pProductVersion!=NULL)
				SetDlgItemText(IDC_VERSION,CStringW(IDS_VERSION)+LPCWSTR(pProductVersion));

			delete[] pData;
		}
		else
		{
			UINT iDataLength=GetFileVersionInfoSize(GetApp()->GetExeName(),NULL);
			BYTE* pData=new BYTE[iDataLength];
			GetFileVersionInfo(GetApp()->GetExeName(),NULL,iDataLength,pData);
			VOID* pTranslations,* pProductVersion=NULL;
			VerQueryValue(pData,"VarFileInfo\\Translation",&pTranslations,&iDataLength);
			char szTranslation[100];
			StringCbPrintf(szTranslation,100,"\\StringFileInfo\\%04X%04X\\ProductVersion",LPWORD(pTranslations)[0],LPWORD(pTranslations)[1]);
			if (!VerQueryValue(pData,szTranslation,&pProductVersion,&iDataLength))
				VerQueryValue(pData,"\\StringFileInfo\\040904b0\\ProductVersion",&pProductVersion,&iDataLength);
			
			if (pProductVersion!=NULL)
				SetDlgItemText(IDC_VERSION,CString(IDS_VERSION)+LPCSTR(pProductVersion));

			delete[] pData;
		}
		

	}
	
	// Use RtlGetVersion for true OS version (GetVersionEx lies after Win8.1)
	RTL_OSVERSIONINFOW rtlver;
	if (GetTrueWindowsVersion(&rtlver))
	{
		if (rtlver.dwMajorVersion >= 10 && rtlver.dwBuildNumber >= 22000)
			text.Format(L"Windows 11 (Version %d.%d Build %d)",
				rtlver.dwMajorVersion, rtlver.dwMinorVersion, rtlver.dwBuildNumber);
		else if (rtlver.dwMajorVersion >= 10)
			text.Format(L"Windows 10 (Version %d.%d Build %d)",
				rtlver.dwMajorVersion, rtlver.dwMinorVersion, rtlver.dwBuildNumber);
		else if (rtlver.dwMajorVersion == 6 && rtlver.dwMinorVersion == 3)
			text.Format(L"Windows 8.1 (Version %d.%d Build %d)",
				rtlver.dwMajorVersion, rtlver.dwMinorVersion, rtlver.dwBuildNumber);
		else if (rtlver.dwMajorVersion == 6 && rtlver.dwMinorVersion == 2)
			text.Format(L"Windows 8 (Version %d.%d Build %d)",
				rtlver.dwMajorVersion, rtlver.dwMinorVersion, rtlver.dwBuildNumber);
		else if (rtlver.dwMajorVersion == 6 && rtlver.dwMinorVersion >= 1)
			text.Format(L"Windows 7 (Version %d.%d Build %d)",
				rtlver.dwMajorVersion, rtlver.dwMinorVersion, rtlver.dwBuildNumber);
		else if (rtlver.dwMajorVersion == 6)
			text.Format(L"Windows Vista (Version %d.%d Build %d)",
				rtlver.dwMajorVersion, rtlver.dwMinorVersion, rtlver.dwBuildNumber);
		else
			text.Format(L"Windows NT %d.%d (Build %d)",
				rtlver.dwMajorVersion, rtlver.dwMinorVersion, rtlver.dwBuildNumber);
	}
	else
	{
		// Fallback to GetVersionEx if RtlGetVersion unavailable
		ver.dwOSVersionInfoSize=sizeof(OSVERSIONINFO);
		if(GetVersionEx(&ver))
			text.Format(L"Windows (Version %d.%d Build %d)",
				ver.dwMajorVersion, ver.dwMinorVersion, ver.dwBuildNumber);
	}

	// Use GlobalMemoryStatusEx for accurate reporting (>4 GB)
	MEMORYSTATUSEX memex;
	memex.dwLength = sizeof(MEMORYSTATUSEX);
	if (GlobalMemoryStatusEx(&memex))
	{
		text2.Format(L"\nPhysical memory: %llu MB total, %llu MB available",
			memex.ullTotalPhys >> 20, memex.ullAvailPhys >> 20);
		text << text2;
		text2.Format(L"\nPage file: %llu MB total, %llu MB available",
			memex.ullTotalPageFile >> 20, memex.ullAvailPageFile >> 20);
		text << text2;
	}
	SetDlgItemText(IDC_SYSINFO,text);
	SetIcon(NULL,TRUE);
	SetIcon(NULL,FALSE);
	return FALSE;
}

void CAboutDlg::OnDrawItem(UINT idCtl,LPDRAWITEMSTRUCT lpdis)
{
	CDialog::OnDrawItem(idCtl,lpdis);
	CDC dc(lpdis->hDC);
	CFont FontRegular,FontUnderline;
	TEXTMETRIC tm;
	char szFace[100];
	dc.GetTextMetrics(&tm);
	dc.GetTextFace(100,szFace);
	
	FontRegular.CreateFont(tm.tmHeight,0,0,0,
		tm.tmWeight,tm.tmItalic,0,tm.tmStruckOut,
		tm.tmCharSet,OUT_CHARACTER_PRECIS,
		CLIP_DEFAULT_PRECIS,DEFAULT_QUALITY,
		tm.tmPitchAndFamily,szFace);
	
	FontUnderline.CreateFont(tm.tmHeight,0,0,0,
		tm.tmWeight,tm.tmItalic,1,tm.tmStruckOut,
		tm.tmCharSet,OUT_CHARACTER_PRECIS,
		CLIP_DEFAULT_PRECIS,DEFAULT_QUALITY,
		tm.tmPitchAndFamily,szFace);
	
	HFONT hOldFont=(HFONT)dc.SelectObject(FontRegular);
	
	
	CStringW text;
	GetDlgItemText(idCtl,text);
	
	RECT rc=lpdis->rcItem;

	LPCWSTR pPtr=text;
	while (*pPtr!=L'\0')
	{
		int nLength=FirstCharIndex(pPtr,L'[');
		
		
		// Paint regular part
		dc.SetTextColor(RGB(0,0,0));
		RECT rc2=rc;
		dc.DrawText(pPtr,nLength,&rc2,DT_LEFT|DT_SINGLELINE|DT_VCENTER|DT_CALCRECT);
		dc.DrawText(pPtr,nLength,&rc2,DT_LEFT|DT_SINGLELINE|DT_VCENTER);
		rc.left=rc2.right;
		
		if (nLength==-1)
			break;

		pPtr+=nLength+1;

		// URL part
		nLength=FirstCharIndex(pPtr,L']');

		
		dc.SetTextColor(RGB(0,0,255));
		dc.SelectObject(FontUnderline);
		rc2=rc;
		dc.DrawText(pPtr,nLength,&rc2,DT_LEFT|DT_SINGLELINE|DT_VCENTER|DT_CALCRECT);
		dc.DrawText(pPtr,nLength,&rc2,DT_LEFT|DT_SINGLELINE|DT_VCENTER);
		rc.left=rc2.right;

		if (nLength==-1)
			break;

		dc.SelectObject(FontRegular);

		pPtr+=nLength+1;
				
	}
			

	dc.SelectObject(hOldFont);

	FontRegular.DeleteObject();
	FontUnderline.DeleteObject();
}

LRESULT CAboutDlg::WindowProc(UINT msg,WPARAM wParam,LPARAM lParam)
{
	switch (msg)
	{
	case WM_ERASEBKGND:
		{
			CRect rect;
			CBrush br;
			GetClientRect(&rect);

			br.CreateSolidBrush(RGB(252,248,240));
			
			FillRect((HDC)wParam,&CRect(0,68,rect.right,rect.bottom),GetSysColorBrush(COLOR_3DFACE));
			FillRect((HDC)wParam,&CRect(0,0,68,rect.bottom),br);
			return 1;
		}
	}
	return CDialog::WindowProc(msg,wParam,lParam);
}

