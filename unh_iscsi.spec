# TODO:
#	- finish it
#
# Conditional build:
%bcond_without	dist_kernel	# allow non-distribution kernel
%bcond_with	kernel		# kernel modules (2.6.x)
%bcond_without	userspace	# userspace package
%bcond_with	verbose		# verbose build (V=1)
#
%define	rel	0.1
Summary:	UNH iSCSI Initiator/Target for Linux
Summary(pl.UTF-8):	Sterowniki UNH iSCSI Initiator/Target dla Linuksa
Name:		unh_iscsi
Version:	2.0
Release:	%{rel}
License:	GPL v2+
Group:		Base/Kernel
Source0:	https://downloads.sourceforge.net/unh-iscsi/unh-iscsi-%{version}.tar.bz2
# Source0-md5:	5759e3a7bafaeb72f2d7ce0992b06f7e
# not found in repo
#Source1:	%{name}.init
#Source2:	%{name}.sysconfig
Patch0:		%{name}-headers.patch
Patch1:		%{name}-sh.patch
Patch2:		%{name}-format.patch
URL:		https://unh-iscsi.sourceforge.net/
%{?with_dist_kernel:BuildRequires:	kernel-headers >= 2.6.0}
BuildRequires:	rpmbuild(macros) >= 1.268
Requires(post,preun):	/sbin/chkconfig
Requires:	rc-scripts
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_sbindir	/sbin

%description
The UNH-iSCSI project consists of software implementations of an
Initiator and Target emulator loadable modules for the IETF Networking
(SAN) protocol (Draft 20).

%description -l pl.UTF-8
Projekt UNH-iSCSI składa się z programowych implementacji emulacji
Initiator i Target jako ładowalnych modułów dla protokołu IETF
Networking (SAN) (draft 20).

%package -n kernel-unh_iscsi
Summary:	UNH ISCSI kernel module
Summary(pl.UTF-8):	Moduł jądra UNH ISCSI
Release:	%{rel}@%{_kernel_ver_str}
Group:		Base/Kernel
Requires:	%{name} = %{version}-%{release}
Obsoletes:	kernel-smp-unh_iscsi < 2

%description -n kernel-unh_iscsi
IP over SCSI kernel module.

%description -n kernel-unh_iscsi -l pl.UTF-8
Moduł jądra dla protokołu IP over SCSI.

%prep
%setup -q -n unh-iscsi-%{version}
%patch0 -p1
%patch1 -p1
%patch2 -p1

%{__sed} -i -e 's/ -Werror//' Makefile-user

%build
%if %{with kernel}
echo "#define OUR_NAME \"PLD Linux %{name}/%{version} for kernel %{_kernel_ver_str}.\"" > initiator/version.h

# kernel module(s)
if [ ! -r "%{_kernelsrcdir}/.config" ]; then
	exit 1
fi
rm -rf include
install -d include/{linux,config}
ln -sf %{_kernelsrcdir}/include/linux/autoconf.h include/linux/autoconf.h
ln -sf %{_kernelsrcdir}/include/asm-%{_target_base_arch} include/asm
ln -sf %{_kernelsrcdir}/Module.symvers Module.symvers
touch include/config/MARKER

%{__make} -C %{_kernelsrcdir} clean \
	RCS_FIND_IGNORE="-name '*.ko' -o" \
	M=$PWD O=$PWD \
	%{?with_verbose:V=1}
%{__make} -C %{_kernelsrcdir} modules \
	M=$PWD O=$PWD \
	%{?with_verbose:V=1}
%endif

CFLAGS="%{rpmcflags} -D_DEFAULT_SOURCE" \
%{__make} -f Makefile-user \
	CC="%{__cc}"

%{__make} -C cmd \
	CC="%{__cc}" \
	CFLAGS="%{rpmcflags} -D_DEFAULT_SOURCE"

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_sbindir},%{_mandir}/man{1,5,8},/etc/{rc.d/init.d,sysconfig}}

%if %{with kernel}
install -d $RPM_BUILD_ROOT/lib/modules/%{_kernel_ver}{,smp}/misc
for mod in unh_iscsi_initiator unh_iscsi_target unh_scsi_target; do
	install ${mod}.ko \
		$RPM_BUILD_ROOT/lib/modules/%{_kernel_ver}/misc/${mod}.ko
done
%endif

#install %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/%{name}
#cp -p %{SOURCE2} $RPM_BUILD_ROOT/etc/sysconfig/%{name}

install cmd/{iscsi_config,iscsi_connect,iscsi_disconnect,iscsi_manage,iscsi_mount,iscsi_rebuild,iscsi_test,iscsi_umount} \
	$RPM_BUILD_ROOT%{_sbindir}

%clean
rm -rf $RPM_BUILD_ROOT

%post -n kernel-unh_iscsi
%depmod %{_kernel_ver}

%postun -n kernel-unh_iscsi
%depmod %{_kernel_ver}

%post
/sbin/chkconfig --add %{name}
#%%service %{name} start

%preun
if [ "$1" = "0" ]; then
	%service %{name} stop
	/sbin/chkconfig --del %{name}
fi

%if %{with userspace}
%files
%defattr(644,root,root,755)
%doc CHANGELOG README TODO docs/{DISKIO_MODE,ENTRY-POINTS-INI,FIELD.GRID,INI-*,ISCSI_*,KEY.GRID,OVERVIEW*,TARGET_*,USER_SPACE,crc_v3.txt,iSER_MEMORY,iscsi_manage_keys}
%attr(755,root,root) %{_sbindir}/iscsi_config
%attr(755,root,root) %{_sbindir}/iscsi_connect
%attr(755,root,root) %{_sbindir}/iscsi_disconnect
%attr(755,root,root) %{_sbindir}/iscsi_manage
%attr(755,root,root) %{_sbindir}/iscsi_mount
%attr(755,root,root) %{_sbindir}/iscsi_rebuild
%attr(755,root,root) %{_sbindir}/iscsi_test
%attr(755,root,root) %{_sbindir}/iscsi_umount
#%attr(754,root,root) /etc/rc.d/init.d/%{name}
#%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/%{name}
%endif

%if %{with kernel}
%files -n kernel-unh_iscsi
%defattr(644,root,root,755)
/lib/modules/%{_kernel_ver}/misc/unh_iscsi_initiator.ko*
/lib/modules/%{_kernel_ver}/misc/unh_iscsi_target.ko*
/lib/modules/%{_kernel_ver}/misc/unh_scsi_target.ko*
%endif
